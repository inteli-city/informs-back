from copy import deepcopy
from typing import List, Optional

from src.shared.domain.entities.system_group import SystemGroup
from src.shared.domain.repositories.system_group_repository_interface import ISystemGroupRepository


MOCK_GROUP_A_ID = "equipe-a"
MOCK_GROUP_B_ID = "equipe-b"


class SystemGroupRepositoryMock(ISystemGroupRepository):
    """Implementação em memória usada nos testes. Pré-popula GAIA com os
    grupos A e B do cenário de evidência do IN-1.1 (ADR-0022)."""

    groups: List[SystemGroup]

    def __init__(self):
        self.groups = [
            SystemGroup(system="GAIA", group_id=MOCK_GROUP_A_ID, name="Equipe A",
                        created_at=946684800000, updated_at=946684800000),
            SystemGroup(system="GAIA", group_id=MOCK_GROUP_B_ID, name="Equipe B",
                        created_at=946684800000, updated_at=946684800000),
        ]

    def get_group(self, system: str, group_id: str) -> Optional[SystemGroup]:
        for group in self.groups:
            if group.system == system and group.group_id == group_id:
                return deepcopy(group)
        return None

    def list_groups(self, system: str) -> List[SystemGroup]:
        return [deepcopy(group) for group in self.groups if group.system == system]

    def put_group(self, group: SystemGroup) -> SystemGroup:
        self.groups = [g for g in self.groups if not (g.system == group.system and g.group_id == group.group_id)]
        self.groups.append(deepcopy(group))
        return deepcopy(group)

    def delete_group(self, system: str, group_id: str) -> None:
        self.groups = [g for g in self.groups if not (g.system == system and g.group_id == group_id)]
