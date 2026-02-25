from abc import ABC, abstractmethod
from typing import Optional, Tuple


class IOriginRepository(ABC):

    @abstractmethod
    def sync_form(
        self,
        origin_system: str,
        payload: dict,
        execution_id: Optional[str] = None,
        logger: Optional[object] = None,
    ) -> Tuple[bool, int, str]:
        pass
