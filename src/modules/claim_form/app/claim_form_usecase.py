import uuid
from typing import List, Optional

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.form_event import FormEvent
from src.shared.domain.enums.assignment_source_enum import AssignmentSource
from src.shared.domain.enums.form_event_type_enum import FormEventType
from src.shared.domain.repositories.form_event_repository_interface import IFormEventRepository
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


class ClaimFormUsecase:
    """Reivindica uma OS do pool (RN-UBE-001/002, especificação Uberlândia §6)."""

    def __init__(
        self,
        form_repo: IFormRepository,
        form_event_repo: IFormEventRepository,
        access_control: Optional[AccessControl] = None,
    ):
        self.form_repo = form_repo
        self.form_event_repo = form_event_repo
        self.access_control = access_control

    def __call__(self, requester_user_id: str, requester_systems: Optional[List[str]], form_id: str) -> Form:
        form = self.form_repo.get_form_by_id(user_id=requester_user_id, form_id=form_id)
        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        if requester_systems is not None and form.system not in requester_systems:
            raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")
        # ADR-0022: OS aberta com grupos só é pega por quem está num deles.
        # O gestor que quiser direcioná-la usa o assign.
        if form.groups and self.access_control is not None and not form.is_open_to_groups(
            self.access_control.groups_in(requester_user_id, form.system)
        ):
            raise ForbiddenAction("Formulário destinado a um grupo em que você não está")

        now_ms = now_timestamp_ms()
        claimed = self.form_repo.claim_form(
            form_id=form_id,
            user_id=requester_user_id,
            claimed_at=now_ms,
            updated_at=now_ms,
            source=AssignmentSource.CLAIM,
        )
        if claimed is None:
            raise NoItemsFound("Formulário não encontrado")

        self.form_event_repo.create_event(FormEvent(
            id=str(uuid.uuid4()),
            form_id=form_id,
            event_type=FormEventType.CLAIMED,
            actor_user_id=requester_user_id,
            created_at=now_ms,
        ))
        return claimed
