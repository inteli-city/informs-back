from copy import deepcopy
from typing import List, Optional

from src.shared.domain.entities.system_config import SystemConfig
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository


class SystemConfigRepositoryMock(ISystemConfigRepository):
    """
    Vazio por padrão: nenhum `system` tem config cadastrada, então
    `get_by_system` sempre devolve `None` — o mesmo comportamento que o
    Gaia tem hoje, sem setup extra em nenhum teste existente.
    """

    configs: List[SystemConfig]

    def __init__(self):
        self.configs = []

    def get_by_system(self, system: str) -> Optional[SystemConfig]:
        for config in self.configs:
            if config.system == system:
                return deepcopy(config)
        return None

    def put(self, config: SystemConfig) -> SystemConfig:
        self.configs = [c for c in self.configs if c.system != config.system]
        self.configs.append(deepcopy(config))
        return deepcopy(config)
