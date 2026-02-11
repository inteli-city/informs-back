from abc import ABC, abstractmethod
from typing import Tuple


class IOriginRepository(ABC):

    @abstractmethod
    def sync_form(self, origin_system: str, payload: dict) -> Tuple[bool, int, str]:
        pass
