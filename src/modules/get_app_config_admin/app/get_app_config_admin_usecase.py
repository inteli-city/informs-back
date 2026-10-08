from dataclasses import dataclass
from typing import Any, Dict, List

from src.shared.domain.entities.app_config import AppConfig
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository
from src.shared.domain.services.app_config_admin import get_admin_profile
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


@dataclass(frozen=True)
class AdminLayer:
    values: Dict[str, Any]
    version: int


@dataclass(frozen=True)
class AdminSystemLayer(AdminLayer):
    system: str
    effective: AppConfig


@dataclass(frozen=True)
class AppConfigAdminResult:
    default_layer: AdminLayer
    can_edit_default: bool
    systems: List[AdminSystemLayer]


class GetAppConfigAdminUsecase:
    """
    O que o editor do Admin precisa: o padrão da aplicação e, para cada sistema
    que a pessoa administra, a camada do sistema (só as diferenças) e a
    configuração efetiva.

    O admin da plataforma vê todo sistema conhecido: os que já têm
    configuração gravada, os do próprio login e os que administra. Assim
    também consegue ver quantos sistemas herdam uma chave do padrão.
    """

    def __init__(self, profile_repo: IProfileRepository, system_config_repo: ISystemConfigRepository):
        self.profile_repo = profile_repo
        self.system_config_repo = system_config_repo

    def __call__(self, requester: UserGatewayDTO) -> AppConfigAdminResult:
        profile = get_admin_profile(self.profile_repo, requester.user_id)

        default = self.system_config_repo.get_default_app_config()
        default_layer = AdminLayer(values=default.values if default else {}, version=default.version if default else 0)

        stored = {config.system: config for config in self.system_config_repo.list_all()}
        if profile.is_platform_admin():
            systems = sorted(set(stored) | set(requester.systems) | set(profile.admin_systems))
        else:
            systems = list(profile.admin_systems)

        layers = []
        for system in systems:
            config = stored.get(system)
            values = config.app_config if config else {}
            layers.append(
                AdminSystemLayer(
                    system=system,
                    values=values,
                    version=config.app_config_version if config else 0,
                    effective=AppConfig.resolve(default_layer.values, values),
                )
            )

        return AppConfigAdminResult(
            default_layer=default_layer,
            can_edit_default=profile.is_platform_admin(),
            systems=layers,
        )
