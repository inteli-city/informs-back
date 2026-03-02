from abc import ABC, abstractmethod
from typing import Optional, Tuple


class IOriginRepository(ABC):

    @abstractmethod
    def sync_forms(
        self,
        origin_system: str,
        payloads: list[dict],
        execution_id: Optional[str] = None,
        logger: Optional[object] = None,
    ) -> Tuple[bool, int, str]:
        pass
