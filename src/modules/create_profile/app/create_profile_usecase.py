from datetime import datetime, timezone

from src.shared.domain.entities.profile import Profile
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction


class CreateProfileUsecase:
    """
    Cria a pessoa (sem role em nenhum sistema). Só super admin pode chamar.
    O role em cada sistema vem depois, em PUT /systems/{system}/users/{user_id}.
    Falha com DuplicatedItem se já existir um Profile com o mesmo user_id
    (incluindo perfis desativados).
    """

    def __init__(self, profile_repo: IProfileRepository):
        self.profile_repo = profile_repo

    def __call__(self, requester_user_id: str, target_user_id: str, name: str, email: str) -> Profile:
        requester = self.profile_repo.get_by_user_id(requester_user_id)
        if requester is None or not requester.is_active_super_admin():
            raise ForbiddenAction("Apenas super admins podem criar perfis")

        if self.profile_repo.get_by_user_id(target_user_id) is not None:
            raise DuplicatedItem(f"Perfil já existe para user_id={target_user_id}")

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        profile = Profile(
            user_id=target_user_id,
            name=name,
            email=email,
            active=True,
            created_at=now_ms,
            updated_at=now_ms,
        )
        return self.profile_repo.create(profile)
