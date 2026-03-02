from typing import Dict, List

from src.shared.domain.entities.sync_error_form import SyncErrorForm
from src.shared.domain.repositories.sync_error_form_repository_interface import ISyncErrorFormRepository


class SyncErrorFormRepositoryMock(ISyncErrorFormRepository):
    def __init__(self):
        self._items: Dict[str, SyncErrorForm] = {}

    def _key(self, job_name: str, system: str, form_id: str) -> str:
        return f"{job_name}::{system}::{form_id}"

    def upsert_error_form(self, item: SyncErrorForm) -> None:
        self._items[self._key(item.job_name, item.system, item.form_id)] = item

    def list_error_forms(self, job_name: str, system: str) -> List[SyncErrorForm]:
        prefix = f"{job_name}::{system}::"
        return [value for key, value in self._items.items() if key.startswith(prefix)]

    def delete_error_forms(self, job_name: str, system: str, form_ids: List[str]) -> None:
        for form_id in form_ids:
            self._items.pop(self._key(job_name, system, form_id), None)
