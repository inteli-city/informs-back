from typing import List

from src.shared.domain.entities.system_group import SystemGroup
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.system_group_repository_interface import ISystemGroupRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ForbiddenAction


class GetSystemGroupsUsecase:
    """Grupos do sistema (ADR-0022). Pode quem gere os grupos ou quem coloca
    pessoas neles (`groups.manage` ou `users.manage`)."""

    def __init__(self, access_control: AccessControl, group_repo: ISystemGroupRepository):
        self.access_control = access_control
        self.group_repo = group_repo

    def __call__(self, requester_user_id: str, system: str) -> List[SystemGroup]:
        if not any(
            self.access_control.can(requester_user_id, system, action)
            for action in (Action.GROUPS_MANAGE, Action.USERS_MANAGE)
        ):
            raise ForbiddenAction(f"Usuário não pode ver os grupos do sistema {system}")
        return sorted(self.group_repo.list_groups(system), key=lambda group: group.name.casefold())
