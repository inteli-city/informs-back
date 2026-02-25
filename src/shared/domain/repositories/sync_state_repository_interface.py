from abc import ABC, abstractmethod
from typing import Optional

from src.shared.domain.entities.sync_state import SyncState


class ISyncStateRepository(ABC):
    @abstractmethod
    def get_state(self, job_name: str, system: str) -> Optional[SyncState]:
        pass

    @abstractmethod
    def set_state(self, state: SyncState) -> None:
        pass
