from copy import deepcopy
from typing import List, Optional

from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository


MOCK_TECNICO_ROLE_ID = "r-tecnico-gaia"
MOCK_GESTOR_ROLE_ID = "r-gestor-gaia"


class SystemRoleRepositoryMock(ISystemRoleRepository):
    """
    Implementação em memória usada nos testes. Pré-popula GAIA com um role
    padrão de campo ("Técnico") e um de gestão ("Gestor"), casando com os
    vínculos do ProfileRepositoryMock.
    """

    roles: List[SystemRole]

    def __init__(self):
        self.roles = [
            SystemRole(
                system="GAIA",
                role_id=MOCK_TECNICO_ROLE_ID,
                name="Técnico",
                actions=[Action.TRACKING_START],
                is_default=True,
                created_at=946684800000,
                updated_at=946684800000,
            ),
            SystemRole(
                system="GAIA",
                role_id=MOCK_GESTOR_ROLE_ID,
                name="Gestor",
                actions=[Action.FORMS_VIEW_ALL, Action.FORMS_ASSIGN, Action.FORMS_RELEASE, Action.TRACKING_VIEW],
                created_at=946684800000,
                updated_at=946684800000,
            ),
        ]

    def get_role(self, system: str, role_id: str) -> Optional[SystemRole]:
        for role in self.roles:
            if role.system == system and role.role_id == role_id:
                return deepcopy(role)
        return None

    def list_roles(self, system: str) -> List[SystemRole]:
        return [deepcopy(role) for role in self.roles if role.system == system]

    def put_role(self, role: SystemRole) -> SystemRole:
        self.roles = [r for r in self.roles if not (r.system == role.system and r.role_id == role.role_id)]
        self.roles.append(deepcopy(role))
        return deepcopy(role)

    def delete_role(self, system: str, role_id: str) -> None:
        self.roles = [r for r in self.roles if not (r.system == system and r.role_id == role_id)]
