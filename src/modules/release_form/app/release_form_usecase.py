import uuid
from typing import List, Optional

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.form_event import FormEvent
from src.shared.domain.enums.form_event_type_enum import FormEventType
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.domain.repositories.form_event_repository_interface import IFormEventRepository
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ErrorWithFile, ForbiddenAction, NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms
from src.shared.helpers.functions.s3_url import extract_file_path


class ReleaseFormUsecase:
    """
    Devolve uma OS ao pool (RN-UBE-004/005). O dono, ou quem tem
    `forms.release` no sistema da OS, pode devolver. O conteúdo é descartado (decisão P5) e os arquivos já
    enviados são removidos do S3 (RN-UBE-012) — `reconcile_form_files`
    continua como rede de segurança, não como mecanismo principal.
    """

    def __init__(
        self,
        form_repo: IFormRepository,
        file_repo: IFileRepository,
        access_control: AccessControl,
        form_event_repo: IFormEventRepository,
    ):
        self.form_repo = form_repo
        self.file_repo = file_repo
        self.access_control = access_control
        self.form_event_repo = form_event_repo

    def __call__(self, requester_user_id: str, requester_systems: Optional[List[str]], form_id: str) -> Form:
        form = self.form_repo.get_form_by_id(user_id=requester_user_id, form_id=form_id)
        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        if requester_systems is not None and form.system not in requester_systems:
            raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")
        self._ensure_can_release(requester_user_id, form)

        file_paths = {
            path for stored in form.stored_files()
            if (path := extract_file_path(stored.file_url)) is not None
        }

        now_ms = now_timestamp_ms()
        form.release(released_at=now_ms, updated_at=now_ms)

        updated = self.form_repo.release_form(
            form_id=form_id, sections=form.sections, released_at=form.released_at, updated_at=form.updated_at,
        )
        if updated is None:
            raise NoItemsFound("Formulário não encontrado")

        # Best-effort: reconcile_form_files é a rede de segurança pra qualquer
        # órfão que sobre daqui (S3 fora do ar, etc.) — não vale derrubar uma
        # devolução que já persistiu por causa de uma falha de limpeza.
        try:
            self.file_repo.delete_files(file_paths)
        except ErrorWithFile:
            pass

        self.form_event_repo.create_event(FormEvent(
            id=str(uuid.uuid4()),
            form_id=form_id,
            event_type=FormEventType.RELEASED,
            actor_user_id=requester_user_id,
            created_at=now_ms,
        ))
        return updated

    def _ensure_can_release(self, requester_user_id: str, form: Form) -> None:
        if form.user_id == requester_user_id:
            return
        if not self.access_control.can(requester_user_id, form.system, Action.FORMS_RELEASE):
            raise ForbiddenAction("Usuário não pode devolver este formulário ao pool")
