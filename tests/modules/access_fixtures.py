"""Cenário comum dos testes das rotas de acesso por sistema (/systems/...).

GAIA tem, além do seed dos mocks:
  - MANAGER_ID com o role "Coordenador" (roles.manage, users.manage,
    tracking.start) — gerencia, mas não é ADMIN;
  - ADMIN_ID com o role ADMIN.
"""

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID, SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.services.access_control import AccessControl
from src.shared.infra.repositories.profile_repository_mock import (
    MOCK_INSPECTOR_ID,
    MOCK_SUPER_ADMIN_ID,
    ProfileRepositoryMock,
)
from src.shared.infra.repositories.system_role_repository_mock import (
    MOCK_GESTOR_ROLE_ID,
    MOCK_TECNICO_ROLE_ID,
    SystemRoleRepositoryMock,
)


SUPER_ADMIN_ID = MOCK_SUPER_ADMIN_ID
INSPECTOR_ID = MOCK_INSPECTOR_ID
MANAGER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120003"
ADMIN_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120004"
COORDENADOR_ROLE_ID = "r-coordenador-gaia"
TECNICO_ROLE_ID = MOCK_TECNICO_ROLE_ID
GESTOR_ROLE_ID = MOCK_GESTOR_ROLE_ID


class AccessScenario:
    def __init__(self):
        self.profile_repo = ProfileRepositoryMock()
        self.role_repo = SystemRoleRepositoryMock()
        self.access_control = AccessControl(self.profile_repo, self.role_repo)

        self.role_repo.put_role(SystemRole(
            system="GAIA", role_id=COORDENADOR_ROLE_ID, name="Coordenador",
            actions=[Action.ROLES_MANAGE, Action.USERS_MANAGE, Action.TRACKING_START],
            created_at=1, updated_at=1,
        ))
        self.add_person(MANAGER_ID, "Maria Coordenadora", "GAIA", COORDENADOR_ROLE_ID)
        self.add_person(ADMIN_ID, "Ana Admin", "GAIA", ADMIN_ROLE_ID)

    def add_person(self, user_id: str, name: str, system: str = None, role_id: str = None) -> None:
        self.profile_repo.create(Profile(
            user_id=user_id, name=name, email=f"{user_id[-4:]}@example.com", active=True,
            created_at=1, updated_at=1,
        ))
        if system:
            self.join(user_id, system, role_id)

    def join(self, user_id: str, system: str, role_id: str) -> None:
        self.profile_repo.put_membership(SystemMembership(
            user_id=user_id, system=system, role_id=role_id, created_at=1, updated_at=1,
        ))


def give_role(profile_repo, role_repo, user_id: str, system: str, actions) -> None:
    """Cria no sistema um role com as ações e dá à pessoa."""
    role = role_repo.put_role(SystemRole(
        system=system, role_id=f"r-{system.lower()}", name="Gestor", actions=actions, created_at=1, updated_at=1,
    ))
    profile_repo.put_membership(SystemMembership(
        user_id=user_id, system=system, role_id=role.role_id, created_at=1, updated_at=1,
    ))


def requester_user(sub: str, groups: str = "FORMULARIOS,GAIA") -> dict:
    return {"sub": sub, "name": "Tester", "email": "tester@example.com", "cognito:groups": groups}
