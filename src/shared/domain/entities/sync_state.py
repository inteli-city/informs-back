from typing import Optional

from src.shared.helpers.errors.domain_errors import EntityError


class SyncState:
    job_name: str
    system: str
    checkpoint_synced_at: int
    status: str
    execution_id: Optional[str]
    started_at: Optional[int]
    ended_at: Optional[int]
    window_end: Optional[int]
    updated_at: int

    VALID_STATUS = {"IDLE", "RUNNING", "COMPLETED", "FAILED"}

    def __init__(
        self,
        job_name: str,
        system: str,
        checkpoint_synced_at: int,
        status: str,
        execution_id: Optional[str],
        started_at: Optional[int],
        ended_at: Optional[int],
        window_end: Optional[int],
        updated_at: int,
    ):
        if not isinstance(job_name, str) or not job_name:
            raise EntityError("job_name")
        self.job_name = job_name

        if not isinstance(system, str) or not system:
            raise EntityError("system")
        self.system = system

        if not isinstance(checkpoint_synced_at, int):
            raise EntityError("checkpoint_synced_at")
        self.checkpoint_synced_at = checkpoint_synced_at

        if not isinstance(status, str) or status not in self.VALID_STATUS:
            raise EntityError("status")
        self.status = status

        if execution_id is not None and (not isinstance(execution_id, str) or not execution_id):
            raise EntityError("execution_id")
        self.execution_id = execution_id

        for key, value in [("started_at", started_at), ("ended_at", ended_at), ("window_end", window_end)]:
            if value is not None and not isinstance(value, int):
                raise EntityError(key)
        self.started_at = started_at
        self.ended_at = ended_at
        self.window_end = window_end

        if not isinstance(updated_at, int):
            raise EntityError("updated_at")
        self.updated_at = updated_at

    @staticmethod
    def make_pk(job_name: str, system: str) -> str:
        return f"sync_state#{job_name}#{system}"

    @staticmethod
    def make_sk() -> str:
        return "METADATA"
