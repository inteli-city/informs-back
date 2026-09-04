from datetime import datetime, timezone
from typing import Dict, List

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


class UpdateProfileUsecase:
    """
    Atualiza `role`/`scope` de um perfil existente. Integração Apex
    (especificação Uberlândia §7.4) — reflete mudanças de permissão
    regional feitas no sistema origem. Apenas ADMIN ativo pode chamar,
    mesmo padrão de `create_profile`/`delete_profile`.
    """

    def __init__(self, profile_repo: IProfileRepository):
        self.profile_repo = profile_repo

    def __call__(
        self,
        requester_user_id: str,
        target_user_id: str,
        role: ProfileRole,
        scope: Dict[str, List[str]],
    ) -> Profile:
        self._ensure_requester_is_active_admin(requester_user_id)

        target = self.profile_repo.get_by_user_id(target_user_id)
        if target is None:
            raise NoItemsFound(f"Perfil não encontrado para user_id={target_user_id}")

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        return self.profile_repo.update_profile(
            user_id=target_user_id, role=role, scope=scope, updated_at=now_ms
        )

    def _ensure_requester_is_active_admin(self, requester_user_id: str) -> None:
        requester_profile = self.profile_repo.get_by_user_id(requester_user_id)
        if requester_profile is None or not requester_profile.active or requester_profile.role != ProfileRole.ADMIN:
            raise ForbiddenAction("Apenas administradores ativos podem atualizar perfis")
