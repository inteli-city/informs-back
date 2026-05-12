from copy import deepcopy
from typing import List, Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import PROFILE_ROLE
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound


class ProfileRepositoryMock(IProfileRepository):
    """
    Implementação em memória usada nos testes. Pré-popula com 1 ADMIN e 1
    INSPECTOR para que cenários comuns possam ser cobertos sem setup extra.
    Cópias profundas são retornadas/aceitas para evitar mutação cruzada
    entre testes.
    """

    profiles: List[Profile]

    def __init__(self):
        self.profiles = [
            Profile(
                user_id="d61dbf66-a10f-11ed-a8fc-0242ac120001",
                role=PROFILE_ROLE.ADMIN,
                name="Admin Mock",
                email="admin@example.com",
                system="GAIA",
                active=True,
                created_at=946684800000,
                updated_at=946684800000,
                vehicle_plate=None,
            ),
            Profile(
                user_id="d61dbf66-a10f-11ed-a8fc-0242ac120002",
                role=PROFILE_ROLE.INSPECTOR,
                name="Inspector Mock",
                email="inspector@example.com",
                system="GAIA",
                active=True,
                created_at=946684800000,
                updated_at=946684800000,
                vehicle_plate="ABC1D23",
            ),
        ]

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

    def count_active_by_role(self, role: PROFILE_ROLE) -> int:
        return sum(1 for p in self.profiles if p.role == role and p.active)
