"""Cenário dos testes das rotas de grupos (ADR-0022), sobre o AccessScenario.

Em GAIA, além do AccessScenario:
  - os grupos A e B do SystemGroupRepositoryMock;
  - GROUPS_MANAGER_ID com um role só com `groups.manage`.
"""

from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.system_group_repository_mock import (
    MOCK_GROUP_A_ID,
    MOCK_GROUP_B_ID,
    SystemGroupRepositoryMock,
)
from tests.modules.access_fixtures import AccessScenario


GROUP_A_ID = MOCK_GROUP_A_ID
GROUP_B_ID = MOCK_GROUP_B_ID
GROUPS_MANAGER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120005"
GRUPOS_ROLE_ID = "r-grupos-gaia"


class GroupScenario(AccessScenario):
    def __init__(self):
        super().__init__()
        self.group_repo = SystemGroupRepositoryMock()
        self.form_repo = FormRepositoryMock()
        self.role_repo.put_role(SystemRole(
            system="GAIA", role_id=GRUPOS_ROLE_ID, name="Grupos", actions=[Action.GROUPS_MANAGE],
            created_at=1, updated_at=1,
        ))
        self.add_person(GROUPS_MANAGER_ID, "Gil Grupos", "GAIA", GRUPOS_ROLE_ID)

    def set_groups(self, user_id: str, system: str, groups) -> None:
        membership = self.profile_repo.get_membership(user_id, system)
        membership.groups = list(groups)
        self.profile_repo.put_membership(membership)
