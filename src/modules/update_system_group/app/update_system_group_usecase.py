from src.shared.domain.entities.system_group import SystemGroup
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.system_group_repository_interface import ISystemGroupRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.role_management import ensure_can
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


class UpdateSystemGroupUsecase:
    """Renomeia um grupo (ADR-0022). O `group_id` não muda: é o que o sistema
    de origem manda no POST /forms."""

    def __init__(self, access_control: AccessControl, group_repo: ISystemGroupRepository):
        self.access_control = access_control
        self.group_repo = group_repo

    def __call__(self, requester_user_id: str, system: str, group_id: str, name: str) -> SystemGroup:
        ensure_can(self.access_control, requester_user_id, system, Action.GROUPS_MANAGE)

        current = self.group_repo.get_group(system, group_id)
        if current is None:
            raise NoItemsFound(f"Grupo {group_id} não encontrado no sistema {system}")
        if any(
            group.group_id != group_id and group.name.casefold() == name.strip().casefold()
            for group in self.group_repo.list_groups(system)
        ):
            raise DuplicatedItem(f"Já existe um grupo chamado {name.strip()} no sistema {system}")

        group = SystemGroup(
            system=system, group_id=group_id, name=name,
            created_at=current.created_at, updated_at=now_timestamp_ms(),
        )
        return self.group_repo.put_group(group)
