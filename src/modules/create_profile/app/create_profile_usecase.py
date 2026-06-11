from datetime import datetime, timezone
from typing import Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction


class CreateProfileUsecase:
    """
    Cria um novo Profile (ADMIN ou INSPECTOR). Apenas ADMIN ativos podem
    chamar. Falha com DuplicatedItem se já existir um Profile com o mesmo
    user_id (incluindo perfis previamente desativados — não há "reativar"
    neste PR; v2 trará UPDATE).
    """

    def __init__(self, profile_repo: IProfileRepository):
        self.profile_repo = profile_repo

    def __call__(
        self,
        requester_user_id: str,
        target_user_id: str,
        role: ProfileRole,
        name: str,
        email: str,
        system: str,
        vehicle_plate: Optional[str] = None,
    ) -> Profile:
        self._ensure_requester_is_active_admin(requester_user_id)

        existing = self.profile_repo.get_by_user_id(target_user_id)
        if existing is not None:
            raise DuplicatedItem(f"Perfil já existe para user_id={target_user_id}")

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        profile = Profile(
            user_id=target_user_id,
            role=role,
            name=name,
            email=email,
            system=system,
            vehicle_plate=vehicle_plate,
            active=True,
            created_at=now_ms,
            updated_at=now_ms,
        )
        return self.profile_repo.create(profile)

    def _ensure_requester_is_active_admin(self, requester_user_id: str) -> None:
        requester_profile = self.profile_repo.get_by_user_id(requester_user_id)
        if requester_profile is None or not requester_profile.active or requester_profile.role != ProfileRole.ADMIN:
            raise ForbiddenAction("Apenas administradores ativos podem criar perfis")
