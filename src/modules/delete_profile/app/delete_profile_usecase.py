from datetime import datetime, timezone

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound


class DeleteProfileUsecase:
    """
    Soft delete de perfil. Regras:

    1. Apenas ADMIN ativo pode chamar.
    2. Não é permitido auto-deletar (admin não pode se "trancar do lado de fora").
    3. Não é permitido remover o ÚLTIMO admin ativo (sistema sempre precisa
       de pelo menos um admin para futuras operações de gestão).
    4. Se o profile alvo já estiver `active=False`, retorna DuplicatedItem
       (não há "deletar duas vezes").

    O DELETE é soft: marca `active=False` e atualiza `updated_at`.
    """

    def __init__(self, profile_repo: IProfileRepository):
        self.profile_repo = profile_repo

    def __call__(self, requester_user_id: str, target_user_id: str) -> Profile:
        self._ensure_requester_is_active_admin(requester_user_id)

        if requester_user_id == target_user_id:
            raise ForbiddenAction("Administradores não podem desativar o próprio perfil")

        target = self.profile_repo.get_by_user_id(target_user_id)
        if target is None:
            raise NoItemsFound(f"Perfil não encontrado para user_id={target_user_id}")
        if not target.active:
            raise DuplicatedItem(f"Perfil já está desativado para user_id={target_user_id}")

        if target.role == ProfileRole.ADMIN:
            active_admins = self.profile_repo.count_active_by_role(ProfileRole.ADMIN)
            if active_admins <= 1:
                raise ForbiddenAction("Não é possível desativar o último administrador ativo")

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        return self.profile_repo.soft_delete(user_id=target_user_id, updated_at=now_ms)

    def _ensure_requester_is_active_admin(self, requester_user_id: str) -> None:
        requester_profile = self.profile_repo.get_by_user_id(requester_user_id)
        if requester_profile is None or not requester_profile.active or requester_profile.role != ProfileRole.ADMIN:
            raise ForbiddenAction("Apenas administradores ativos podem desativar perfis")
