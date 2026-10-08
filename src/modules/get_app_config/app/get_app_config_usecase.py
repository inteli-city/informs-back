from dataclasses import dataclass
from typing import List

from src.shared.domain.entities.app_config import AppConfig
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


@dataclass(frozen=True)
class ResolvedAppConfig:
    version: str
    config: AppConfig


@dataclass(frozen=True)
class SystemResolvedAppConfig(ResolvedAppConfig):
    system: str


@dataclass(frozen=True)
class AppConfigResult:
    default: ResolvedAppConfig
    systems: List[SystemResolvedAppConfig]


class GetAppConfigUsecase:
    """
    Configuração efetiva da aplicação para quem pede: o padrão da aplicação e,
    para cada sistema do usuário, o padrão com as diferenças daquele sistema
    por cima.

    A versão de cada configuração junta a versão das camadas que a compõem
    ("<padrão>.<sistema>"): muda sempre que qualquer uma delas muda, e o app
    usa isso para saber quando baixar de novo.
    """

    def __init__(self, system_config_repo: ISystemConfigRepository):
        self.system_config_repo = system_config_repo

    def __call__(self, requester: UserGatewayDTO) -> AppConfigResult:
        default = self.system_config_repo.get_default_app_config()
        default_values = default.values if default else {}
        default_version = default.version if default else 0

        systems = []
        for system in requester.systems:
            system_config = self.system_config_repo.get_by_system(system)
            system_values = system_config.app_config if system_config else {}
            system_version = system_config.app_config_version if system_config else 0
            systems.append(
                SystemResolvedAppConfig(
                    system=system,
                    version=f"{default_version}.{system_version}",
                    config=AppConfig.resolve(default_values, system_values),
                )
            )

        return AppConfigResult(
            default=ResolvedAppConfig(version=str(default_version), config=AppConfig.resolve(default_values)),
            systems=systems,
        )
