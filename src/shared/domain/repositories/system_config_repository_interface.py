from abc import ABC, abstractmethod
from typing import Optional

from src.shared.domain.entities.default_app_config import DefaultAppConfig
from src.shared.domain.entities.system_config import SystemConfig


class ISystemConfigRepository(ABC):

    @abstractmethod
    def get_by_system(self, system: str) -> Optional[SystemConfig]:
        pass

    @abstractmethod
    def put(self, config: SystemConfig) -> SystemConfig:
        pass

    @abstractmethod
    def get_default_app_config(self) -> Optional[DefaultAppConfig]:
        pass

    @abstractmethod
    def put_default_app_config(self, config: DefaultAppConfig) -> DefaultAppConfig:
        pass
