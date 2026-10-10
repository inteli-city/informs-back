from typing import List

from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.role_management import (
    clear_other_defaults,
    ensure_can,
    ensure_no_escalation,
    ensure_unique_name,
)
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


class CreateSystemRoleUsecase:
    """Cria um role no sistema. Pode quem tem `roles.manage` ali; quem não é
    ADMIN do sistema só usa ações que ele mesmo tem."""

    def __init__(self, access_control: AccessControl, role_repo: ISystemRoleRepository):
        self.access_control = access_control
        self.role_repo = role_repo

    def __call__(
        self, requester_user_id: str, system: str, name: str, actions: List[Action], is_default: bool,
    ) -> SystemRole:
        ensure_can(self.access_control, requester_user_id, system, Action.ROLES_MANAGE)
        ensure_no_escalation(self.access_control, requester_user_id, system, actions)
        ensure_unique_name(self.role_repo, system, name)

        now_ms = now_timestamp_ms()
        role = SystemRole(
            system=system, name=name, actions=actions, is_default=is_default, created_at=now_ms, updated_at=now_ms,
        )
        saved = self.role_repo.put_role(role)
        if is_default:
            clear_other_defaults(self.role_repo, system, keep_role_id=saved.role_id, now_ms=now_ms)
        return saved
