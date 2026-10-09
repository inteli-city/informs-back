import time
from dataclasses import dataclass
from typing import Any, Dict

from src.shared.domain.entities.app_config import AppConfig
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.app_config_admin import STALE_VERSION_MESSAGE
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


@dataclass(frozen=True)
class SystemAppConfigSaved:
    system: str
    values: Dict[str, Any]
    version: int
    effective: AppConfig


class PutSystemAppConfigUsecase:
    """
    Grava as diferenças de um sistema em relação ao padrão. Pode quem tem
    `app_config.edit` no sistema (o ADMIN dele tem) ou o super admin.

    "Voltar ao padrão" é mandar a camada sem aquela chave. Os demais campos da
    SystemConfig (escopo, geofence, allow_unassigned_forms) são preservados.
    """

    def __init__(self, access_control: AccessControl, system_config_repo: ISystemConfigRepository):
        self.access_control = access_control
        self.system_config_repo = system_config_repo

    def __call__(
        self, requester: UserGatewayDTO, system: str, values: Dict[str, Any], base_version: int
    ) -> SystemAppConfigSaved:
        if not self.access_control.can(requester.user_id, system, Action.APP_CONFIG_EDIT):
            raise ForbiddenAction(f"Você não edita a configuração do sistema {system}")

        current = self.system_config_repo.get_by_system(system)
        current_version = current.app_config_version if current else 0
        if base_version != current_version:
            raise DuplicatedItem(STALE_VERSION_MESSAGE)

        now = int(time.time() * 1000)
        saved = self.system_config_repo.put(
            SystemConfig(
                system=system,
                created_at=current.created_at if current else now,
                updated_at=now,
                scope_keys=current.scope_keys if current else None,
                scope_partition_key=current.scope_partition_key if current else None,
                geofence_radius_m=current.geofence_radius_m if current else None,
                allow_unassigned_forms=current.allow_unassigned_forms if current else False,
                app_config=values,
                app_config_version=current_version + 1,
            )
        )

        default = self.system_config_repo.get_default_app_config()
        return SystemAppConfigSaved(
            system=system,
            values=saved.app_config,
            version=saved.app_config_version,
            effective=AppConfig.effective(
                default.values if default else {}, saved.app_config, bool(saved.allow_unassigned_forms)
            ),
        )
