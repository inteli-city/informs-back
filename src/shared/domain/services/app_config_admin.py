from src.shared.domain.entities.profile import Profile
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.helpers.errors.usecase_errors import ForbiddenAction


def get_admin_profile(profile_repo: IProfileRepository, user_id: str) -> Profile:
    """
    Perfil de quem entra no Admin: ativo e admin da plataforma (papel ADMIN) ou
    de ao menos um sistema (`admin_systems`). O que cada um pode editar é
    decidido depois, por sistema (`Profile.can_admin_system`).
    """
    profile = profile_repo.get_by_user_id(user_id)
    if profile is None or not profile.active:
        raise ForbiddenAction("Perfil inativo ou inexistente")
    if not profile.is_platform_admin() and not profile.admin_systems:
        raise ForbiddenAction("Apenas administradores acessam a configuração da aplicação")
    return profile


STALE_VERSION_MESSAGE = (
    "A configuração foi alterada por outra pessoa enquanto você editava. "
    "Recarregue para ver a versão atual e refaça a alteração."
)
