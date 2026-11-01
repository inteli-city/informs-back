from abc import ABC, abstractmethod
from typing import List, Optional

from src.shared.domain.entities.system_group import SystemGroup


class ISystemGroupRepository(ABC):
    """Grupos de pessoas de cada sistema (ADR-0022)."""

    @abstractmethod
    def get_group(self, system: str, group_id: str) -> Optional[SystemGroup]:
        pass

    @abstractmethod
    def list_groups(self, system: str) -> List[SystemGroup]:
        pass

    @abstractmethod
    def put_group(self, group: SystemGroup) -> SystemGroup:
        pass

    @abstractmethod
    def delete_group(self, system: str, group_id: str) -> None:
        pass
