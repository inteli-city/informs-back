from datetime import datetime, timezone

from src.shared.domain.entities.profile import Profile
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound


class DeleteProfileUsecase:
    """
    Soft delete de perfil. Regras:

    1. Apenas super admin ativo pode chamar.
    2. Não é permitido auto-desativar (não se "trancar do lado de fora").
    3. Não é permitido desativar o ÚLTIMO super admin ativo (a plataforma
       sempre precisa de alguém que dê o role ADMIN dos sistemas).
    4. Se o profile alvo já estiver `active=False`, retorna DuplicatedItem
       (não há "deletar duas vezes").

    O DELETE é soft: marca `active=False` e atualiza `updated_at`. Os vínculos
    com os sistemas ficam (histórico); perfil inativo não pode nada.
    """

    def __init__(self, profile_repo: IProfileRepository):
        self.profile_repo = profile_repo

    def __call__(self, requester_user_id: str, target_user_id: str) -> Profile:
        requester = self.profile_repo.get_by_user_id(requester_user_id)
        if requester is None or not requester.is_active_super_admin():
            raise ForbiddenAction("Apenas super admins podem desativar perfis")

        if requester_user_id == target_user_id:
            raise ForbiddenAction("Super admins não podem desativar o próprio perfil")

        target = self.profile_repo.get_by_user_id(target_user_id)
        if target is None:
            raise NoItemsFound(f"Perfil não encontrado para user_id={target_user_id}")
        if not target.active:
            raise DuplicatedItem(f"Perfil já está desativado para user_id={target_user_id}")

        if target.super_admin and self.profile_repo.count_active_super_admins() <= 1:
            raise ForbiddenAction("Não é possível desativar o último super admin ativo")

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        return self.profile_repo.soft_delete(user_id=target_user_id, updated_at=now_ms)
