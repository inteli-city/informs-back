import time
from typing import Any, Dict

from src.shared.domain.entities.default_app_config import DefaultAppConfig
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository
from src.shared.domain.services.app_config_admin import STALE_VERSION_MESSAGE, get_admin_profile
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class PutDefaultAppConfigUsecase:
    """
    Grava o padrão da aplicação. Só o admin da plataforma: a mudança chega na
    hora a todo sistema que não sobrescreveu a chave.

    A camada substitui a anterior inteira (o editor manda o documento todo), e
    `base_version` impede que duas pessoas editando ao mesmo tempo apaguem a
    alteração uma da outra.
    """

    def __init__(self, profile_repo: IProfileRepository, system_config_repo: ISystemConfigRepository):
        self.profile_repo = profile_repo
        self.system_config_repo = system_config_repo

    def __call__(self, requester: UserGatewayDTO, values: Dict[str, Any], base_version: int) -> DefaultAppConfig:
        profile = get_admin_profile(self.profile_repo, requester.user_id)
        if not profile.is_platform_admin():
            raise ForbiddenAction("Apenas o admin da plataforma edita o padrão da aplicação")

        current = self.system_config_repo.get_default_app_config()
        current_version = current.version if current else 0
        if base_version != current_version:
            raise DuplicatedItem(STALE_VERSION_MESSAGE)

        config = DefaultAppConfig(
            values=values,
            version=current_version + 1,
            updated_at=int(time.time() * 1000),
            updated_by=requester.email,
        )
        return self.system_config_repo.put_default_app_config(config)
