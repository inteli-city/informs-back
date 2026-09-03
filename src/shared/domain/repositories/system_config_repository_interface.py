from abc import ABC, abstractmethod
from typing import Optional

from src.shared.domain.entities.system_config import SystemConfig


class ISystemConfigRepository(ABC):

    @abstractmethod
    def get_by_system(self, system: str) -> Optional[SystemConfig]:
        pass

    @abstractmethod
    def put(self, config: SystemConfig) -> SystemConfig:
        pass
