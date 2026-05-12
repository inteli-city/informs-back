from abc import ABC, abstractmethod
from typing import Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import PROFILE_ROLE


class IProfileRepository(ABC):
    """
    Operações mínimas necessárias para o v1 (sem UPDATE):

    - get_by_user_id: busca direta para login e validações.
    - create: usado tanto no admin-create quanto no auto-create do login.
    - soft_delete: marca active=False em vez de remover o item.
    - count_active_admins: necessário para impedir a remoção do último ADMIN.
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
    def count_active_by_role(self, role: PROFILE_ROLE) -> int:
        pass
