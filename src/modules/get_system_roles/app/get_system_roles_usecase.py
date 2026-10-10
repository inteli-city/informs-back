from typing import List

from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ForbiddenAction


class GetSystemRolesUsecase:
    """
    Roles criados pelo sistema. Pode quem cria roles (`roles.manage`) ou
    quem dá roles às pessoas (`users.manage`), que precisa da lista para
    escolher. O ADMIN fixo entra na resposta pelo viewmodel.
    """

    def __init__(self, access_control: AccessControl, role_repo: ISystemRoleRepository):
        self.access_control = access_control
        self.role_repo = role_repo

    def __call__(self, requester_user_id: str, system: str) -> List[SystemRole]:
        actions = self.access_control.access_in(requester_user_id, system).actions
        if Action.ROLES_MANAGE not in actions and Action.USERS_MANAGE not in actions:
            raise ForbiddenAction(f"Usuário não pode ver os roles do sistema {system}")
        return sorted(self.role_repo.list_roles(system), key=lambda role: role.name.casefold())
