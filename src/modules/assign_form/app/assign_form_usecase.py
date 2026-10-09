import uuid
from typing import List, Optional

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.form_event import FormEvent
from src.shared.domain.enums.assignment_source_enum import AssignmentSource
from src.shared.domain.enums.form_event_type_enum import FormEventType
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.form_event_repository_interface import IFormEventRepository
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


class AssignFormUsecase:
    """Quem tem `forms.assign` no sistema da OS atribui diretamente uma OS do
    pool a um usuário (RN-UBE-005)."""

    def __init__(
        self,
        form_repo: IFormRepository,
        access_control: AccessControl,
        form_event_repo: IFormEventRepository,
    ):
        self.form_repo = form_repo
        self.access_control = access_control
        self.form_event_repo = form_event_repo

    def __call__(
        self, requester_user_id: str, requester_systems: Optional[List[str]], form_id: str, target_user_id: str,
    ) -> Form:
        form = self.form_repo.get_form_by_id(user_id=requester_user_id, form_id=form_id)
        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        if requester_systems is not None and form.system not in requester_systems:
            raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")
        if not self.access_control.can(requester_user_id, form.system, Action.FORMS_ASSIGN):
            raise ForbiddenAction("Usuário não pode atribuir formulários do pool neste sistema")

        now_ms = now_timestamp_ms()
        assigned = self.form_repo.claim_form(
            form_id=form_id,
            user_id=target_user_id,
            claimed_at=now_ms,
            updated_at=now_ms,
            source=AssignmentSource.MANAGER,
        )
        if assigned is None:
            raise NoItemsFound("Formulário não encontrado")

        self.form_event_repo.create_event(FormEvent(
            id=str(uuid.uuid4()),
            form_id=form_id,
            event_type=FormEventType.ASSIGNED,
            actor_user_id=requester_user_id,
            target_user_id=target_user_id,
            created_at=now_ms,
        ))
        return assigned
