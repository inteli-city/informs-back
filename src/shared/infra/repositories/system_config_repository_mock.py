from copy import deepcopy
from typing import List, Optional

from src.shared.domain.entities.default_app_config import DefaultAppConfig
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository


class SystemConfigRepositoryMock(ISystemConfigRepository):
    """
    Vazio por padrão: nenhum `system` tem config cadastrada, então
    `get_by_system` sempre devolve `None` — o mesmo comportamento que o
    Gaia tem hoje, sem setup extra em nenhum teste existente.
    """

    configs: List[SystemConfig]
    default_app_config: Optional[DefaultAppConfig]

    def __init__(self):
        self.configs = []
        self.default_app_config = None

    def get_by_system(self, system: str) -> Optional[SystemConfig]:
        for config in self.configs:
            if config.system == system:
                return deepcopy(config)
        return None

    def put(self, config: SystemConfig) -> SystemConfig:
        self.configs = [c for c in self.configs if c.system != config.system]
        self.configs.append(deepcopy(config))
        return deepcopy(config)

    def get_default_app_config(self) -> Optional[DefaultAppConfig]:
        return deepcopy(self.default_app_config)

    def put_default_app_config(self, config: DefaultAppConfig) -> DefaultAppConfig:
        self.default_app_config = deepcopy(config)
        return deepcopy(config)
