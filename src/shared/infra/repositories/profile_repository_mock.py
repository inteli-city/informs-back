from copy import deepcopy
from typing import List, Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound
from src.shared.infra.repositories.system_role_repository_mock import MOCK_TECNICO_ROLE_ID


MOCK_SUPER_ADMIN_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
MOCK_INSPECTOR_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"


class ProfileRepositoryMock(IProfileRepository):
    """
    Implementação em memória usada nos testes. Pré-popula com 1 super admin e
    1 pessoa de campo (role "Técnico" em GAIA) para que cenários comuns
    possam ser cobertos sem setup extra. Cópias profundas são
    retornadas/aceitas para evitar mutação cruzada entre testes.
    """

    profiles: List[Profile]
    memberships: List[SystemMembership]

    def __init__(self):
        self.profiles = [
            Profile(
                user_id=MOCK_SUPER_ADMIN_ID,
                name="Admin Mock",
                email="admin@example.com",
                active=True,
                super_admin=True,
                created_at=946684800000,
                updated_at=946684800000,
            ),
            Profile(
                user_id=MOCK_INSPECTOR_ID,
                name="Inspector Mock",
                email="inspector@example.com",
                active=True,
                created_at=946684800000,
                updated_at=946684800000,
            ),
        ]
        self.memberships = [
            SystemMembership(
                user_id=MOCK_INSPECTOR_ID,
                system="GAIA",
                role_id=MOCK_TECNICO_ROLE_ID,
                created_at=946684800000,
                updated_at=946684800000,
            ),
        ]

    # --- Pessoa ---------------------------------------------------------------

    def get_by_user_id(self, user_id: str) -> Optional[Profile]:
        for profile in self.profiles:
            if profile.user_id == user_id:
                return deepcopy(profile)
        return None

    def create(self, profile: Profile) -> Profile:
        if any(p.user_id == profile.user_id for p in self.profiles):
            raise DuplicatedItem(f"Perfil já existe para user_id={profile.user_id}")
        self.profiles.append(deepcopy(profile))
        return deepcopy(profile)

    def soft_delete(self, user_id: str, updated_at: int) -> Profile:
        for profile in self.profiles:
            if profile.user_id == user_id:
                profile.deactivate(updated_at=updated_at)
                return deepcopy(profile)
        raise NoItemsFound(f"Perfil não encontrado para user_id={user_id}")

    def count_active_super_admins(self) -> int:
        return sum(1 for p in self.profiles if p.is_active_super_admin())

    # --- Vínculos ---------------------------------------------------------

    def get_memberships(self, user_id: str) -> List[SystemMembership]:
        return [deepcopy(m) for m in self.memberships if m.user_id == user_id]

    def get_membership(self, user_id: str, system: str) -> Optional[SystemMembership]:
        for membership in self.memberships:
            if membership.user_id == user_id and membership.system == system:
                return deepcopy(membership)
        return None

    def put_membership(self, membership: SystemMembership) -> SystemMembership:
        self.delete_membership(membership.user_id, membership.system)
        self.memberships.append(deepcopy(membership))
        return deepcopy(membership)

    def delete_membership(self, user_id: str, system: str) -> None:
        self.memberships = [
            m for m in self.memberships if not (m.user_id == user_id and m.system == system)
        ]

    def list_memberships_by_system(self, system: str) -> List[SystemMembership]:
        return [deepcopy(m) for m in self.memberships if m.system == system]

    def count_memberships_by_role(self, system: str, role_id: str) -> int:
        return sum(1 for m in self.memberships if m.system == system and m.role_id == role_id)
