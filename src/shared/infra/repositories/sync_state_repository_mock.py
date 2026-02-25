from typing import Dict, Optional

from src.shared.domain.entities.sync_state import SyncState
from src.shared.domain.repositories.sync_state_repository_interface import ISyncStateRepository


class SyncStateRepositoryMock(ISyncStateRepository):
    def __init__(self):
        self._items: Dict[str, SyncState] = {}

    def _key(self, job_name: str, system: str) -> str:
        return f"{job_name}::{system}"

    def get_state(self, job_name: str, system: str) -> Optional[SyncState]:
        return self._items.get(self._key(job_name, system))

    def set_state(self, state: SyncState) -> None:
        self._items[self._key(state.job_name, state.system)] = state
