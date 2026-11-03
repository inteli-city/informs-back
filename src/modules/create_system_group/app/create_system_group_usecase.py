from src.shared.domain.entities.system_group import SystemGroup
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.system_group_repository_interface import ISystemGroupRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.role_management import ensure_can
from src.shared.helpers.errors.usecase_errors import DuplicatedItem
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


class CreateSystemGroupUsecase:
    """Cria um grupo no sistema (ADR-0022). Pode quem tem `groups.manage` ali."""

    def __init__(self, access_control: AccessControl, group_repo: ISystemGroupRepository):
        self.access_control = access_control
        self.group_repo = group_repo

    def __call__(self, requester_user_id: str, system: str, group_id: str, name: str) -> SystemGroup:
        ensure_can(self.access_control, requester_user_id, system, Action.GROUPS_MANAGE)

        if self.group_repo.get_group(system, group_id) is not None:
            raise DuplicatedItem(f"Já existe o grupo {group_id} no sistema {system}")
        if any(group.name.casefold() == name.strip().casefold() for group in self.group_repo.list_groups(system)):
            raise DuplicatedItem(f"Já existe um grupo chamado {name.strip()} no sistema {system}")

        now_ms = now_timestamp_ms()
        group = SystemGroup(system=system, group_id=group_id, name=name, created_at=now_ms, updated_at=now_ms)
        return self.group_repo.put_group(group)
