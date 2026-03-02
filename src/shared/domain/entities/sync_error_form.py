from typing import Optional

from src.shared.helpers.errors.domain_errors import EntityError


class SyncErrorForm:
    job_name: str
    system: str
    form_id: str
    source_updated_at: Optional[int]
    last_failed_at: int

    def __init__(
        self,
        job_name: str,
        system: str,
        form_id: str,
        source_updated_at: Optional[int],
        last_failed_at: int,
    ):
        if not isinstance(job_name, str) or not job_name:
            raise EntityError("job_name")
        self.job_name = job_name

        if not isinstance(system, str) or not system:
            raise EntityError("system")
        self.system = system

        if not isinstance(form_id, str) or not form_id:
            raise EntityError("form_id")
        self.form_id = form_id

        if source_updated_at is not None and not isinstance(source_updated_at, int):
            raise EntityError("source_updated_at")
        self.source_updated_at = source_updated_at

        if not isinstance(last_failed_at, int):
            raise EntityError("last_failed_at")
        self.last_failed_at = last_failed_at

    @staticmethod
    def make_pk(job_name: str, system: str) -> str:
        return f"sync_error_form#{job_name}#{system}"

    @staticmethod
    def make_sk(form_id: str) -> str:
        return f"form#{form_id}"
