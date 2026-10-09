from typing import List

from src.shared.domain.entities.system_role import ADMIN_ROLE_ID, SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.role_management import (
    clear_other_defaults,
    ensure_can,
    ensure_no_escalation,
    ensure_unique_name,
)
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


class UpdateSystemRoleUsecase:
    """
    Substitui nome, ações e `is_default` de um role. O ADMIN é fixo e não se
    edita. Quem não é ADMIN do sistema só mexe em role cujas ações (antes e
    depois) ele mesmo tem.

    A mudança vale na hora para todas as pessoas com o role.
    """

    def __init__(self, access_control: AccessControl, role_repo: ISystemRoleRepository):
        self.access_control = access_control
        self.role_repo = role_repo

    def __call__(
        self, requester_user_id: str, system: str, role_id: str, name: str, actions: List[Action], is_default: bool,
    ) -> SystemRole:
        ensure_can(self.access_control, requester_user_id, system, Action.ROLES_MANAGE)
        if role_id == ADMIN_ROLE_ID:
            raise ForbiddenAction("O role ADMIN é fixo e não pode ser editado")

        current = self.role_repo.get_role(system, role_id)
        if current is None:
            raise NoItemsFound(f"Role {role_id} não encontrado no sistema {system}")

        ensure_no_escalation(self.access_control, requester_user_id, system, [*current.actions, *actions])
        ensure_unique_name(self.role_repo, system, name, ignore_role_id=role_id)

        now_ms = now_timestamp_ms()
        saved = self.role_repo.put_role(SystemRole(
            system=system,
            role_id=role_id,
            name=name,
            actions=actions,
            is_default=is_default,
            created_at=current.created_at,
            updated_at=now_ms,
        ))
        if is_default:
            clear_other_defaults(self.role_repo, system, keep_role_id=role_id, now_ms=now_ms)
        return saved
