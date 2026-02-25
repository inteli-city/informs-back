from abc import ABC, abstractmethod
from typing import List

from src.shared.domain.entities.sync_error_form import SyncErrorForm


class ISyncErrorFormRepository(ABC):
    @abstractmethod
    def upsert_error_form(self, item: SyncErrorForm) -> None:
        pass

    @abstractmethod
    def list_error_forms(self, job_name: str, system: str) -> List[SyncErrorForm]:
        pass

    @abstractmethod
    def delete_error_forms(self, job_name: str, system: str, form_ids: List[str]) -> None:
        pass
