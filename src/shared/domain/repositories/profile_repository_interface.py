from abc import ABC, abstractmethod
from typing import List, Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_membership import SystemMembership


class IProfileRepository(ABC):
    """
    Pessoas e seus vínculos com os sistemas (o role de cada uma em cada
    sistema).

    - get_by_user_id / create / soft_delete: a pessoa.
    - count_active_super_admins: impede desativar o último super admin.
    - *_membership(s): o vínculo pessoa ↔ sistema.
    """

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Optional[Profile]:
        pass

    @abstractmethod
    def create(self, profile: Profile) -> Profile:
        pass

    @abstractmethod
    def soft_delete(self, user_id: str, updated_at: int) -> Profile:
        pass

    @abstractmethod
    def count_active_super_admins(self) -> int:
        pass

    @abstractmethod
    def get_memberships(self, user_id: str) -> List[SystemMembership]:
        pass

    @abstractmethod
    def get_membership(self, user_id: str, system: str) -> Optional[SystemMembership]:
        pass

    @abstractmethod
    def put_membership(self, membership: SystemMembership) -> SystemMembership:
        pass

    @abstractmethod
    def delete_membership(self, user_id: str, system: str) -> None:
        pass

    @abstractmethod
    def list_memberships_by_system(self, system: str) -> List[SystemMembership]:
        pass

    @abstractmethod
    def count_memberships_by_role(self, system: str, role_id: str) -> int:
        pass
