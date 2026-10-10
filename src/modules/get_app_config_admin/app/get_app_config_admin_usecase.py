from dataclasses import dataclass
from typing import Any, Dict, List

from src.shared.domain.entities.app_config import AppConfig
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.app_config_admin import editable_systems
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

    O super admin vê todo sistema conhecido: os que já têm configuração
    gravada e os do próprio login. Assim também consegue ver quantos sistemas
    herdam uma chave do padrão. Quem não é super admin vê só os sistemas em
    que tem `app_config.edit` (lidos um a um, sem varrer a tabela).
    """

    def __init__(self, access_control: AccessControl, system_config_repo: ISystemConfigRepository):
        self.access_control = access_control
        self.system_config_repo = system_config_repo

    def __call__(self, requester: UserGatewayDTO) -> AppConfigAdminResult:
        own_systems = editable_systems(self.access_control, requester.user_id)
        is_super_admin = self.access_control.is_super_admin(requester.user_id)

        default = self.system_config_repo.get_default_app_config()
        default_layer = AdminLayer(values=default.values if default else {}, version=default.version if default else 0)

        if is_super_admin:
            stored = {config.system: config for config in self.system_config_repo.list_all()}
            systems = sorted(set(stored) | set(requester.systems) | set(own_systems))
        else:
            systems = sorted(own_systems)
            stored = {system: self.system_config_repo.get_by_system(system) for system in systems}

        layers = []
        for system in systems:
            config = stored.get(system)
            values = config.app_config if config else {}
            layers.append(
                AdminSystemLayer(
                    system=system,
                    values=values,
                    version=config.app_config_version if config else 0,
                    # Mesma conta do GET /app-config: o Admin mostra o que o app recebe
                    # (ex.: "em aberto" desligado se o sistema não aceita sem dono).
                    effective=AppConfig.effective(
                        default_layer.values, values, bool(config and config.allow_unassigned_forms)
                    ),
                )
            )

        return AppConfigAdminResult(
            default_layer=default_layer,
            can_edit_default=is_super_admin,
            systems=layers,
        )
