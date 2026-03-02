import os
import sys

sys.path.append(os.getcwd())

from src.shared.domain.entities.sync_state import SyncState
from src.shared.infra.repositories.sync_state_repository_mock import SyncStateRepositoryMock


def test_sync_state_repository_mock_get_set():
    repo = SyncStateRepositoryMock()

    assert repo.get_state("sync_forms_origin", "GAIA") is None

    state = SyncState(
        job_name="sync_forms_origin",
        system="GAIA",
        checkpoint_synced_at=12345,
        status="COMPLETED",
        execution_id="exec-1",
        started_at=1000,
        ended_at=2000,
        window_end=2000,
        updated_at=2000,
    )
    repo.set_state(state)

    loaded = repo.get_state("sync_forms_origin", "GAIA")
    assert loaded is not None
    assert loaded.checkpoint_synced_at == 12345
    assert loaded.status == "COMPLETED"
    assert loaded.execution_id == "exec-1"
