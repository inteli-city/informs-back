import time
from dataclasses import dataclass
from typing import Any, Dict

from src.shared.domain.entities.app_config import AppConfig
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository
from src.shared.domain.services.app_config_admin import STALE_VERSION_MESSAGE, get_admin_profile
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
    Grava as diferenças de um sistema em relação ao padrão. Pode quem
    administra o sistema (`admin_systems`) ou o admin da plataforma.

    "Voltar ao padrão" é mandar a camada sem aquela chave. Os demais campos da
    SystemConfig (escopo, geofence, allow_unassigned_forms) são preservados.
    """

    def __init__(self, profile_repo: IProfileRepository, system_config_repo: ISystemConfigRepository):
        self.profile_repo = profile_repo
        self.system_config_repo = system_config_repo

    def __call__(
        self, requester: UserGatewayDTO, system: str, values: Dict[str, Any], base_version: int
    ) -> SystemAppConfigSaved:
        profile = get_admin_profile(self.profile_repo, requester.user_id)
        if not profile.can_admin_system(system):
            raise ForbiddenAction(f"Você não administra o sistema {system}")

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
