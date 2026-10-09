from abc import ABC, abstractmethod
from typing import List, Optional

from src.shared.domain.entities.system_role import SystemRole


class ISystemRoleRepository(ABC):
    """Roles criados por cada sistema (o ADMIN fixo não é gravado)."""

    @abstractmethod
    def get_role(self, system: str, role_id: str) -> Optional[SystemRole]:
        pass

    @abstractmethod
    def list_roles(self, system: str) -> List[SystemRole]:
        pass

    @abstractmethod
    def put_role(self, role: SystemRole) -> SystemRole:
        pass

    @abstractmethod
    def delete_role(self, system: str, role_id: str) -> None:
        pass
