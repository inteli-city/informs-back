import os
import sys

sys.path.append(os.getcwd())

from src.shared.domain.entities.sync_state import SyncState
from src.shared.infra.repositories.sync_state_repository_dynamo import SyncStateRepositoryDynamo


class FakeSyncStateDynamo:
    def __init__(self):
        self.get_item_response = {}
        self.put_calls = []

    def get_item(self, partition_key, sort_key):
        return self.get_item_response

    def put_item(self, item, partition_key, sort_key, is_decimal=False):
        self.put_calls.append((item, partition_key, sort_key, is_decimal))
        return {"ok": True}


def _make_repo():
    repo = SyncStateRepositoryDynamo.__new__(SyncStateRepositoryDynamo)
    repo.dynamo = FakeSyncStateDynamo()
    return repo


def test_sync_state_repository_dynamo_get_state():
    repo = _make_repo()
    repo.dynamo.get_item_response = {}
    assert repo.get_state("sync_forms_origin", "GAIA") is None

    repo.dynamo.get_item_response = {
        "Item": {
            "PK": "sync_state#sync_forms_origin#GAIA",
            "SK": "METADATA",
            "checkpoint_synced_at": 555,
            "status": "COMPLETED",
            "execution_id": "exec-1",
            "started_at": 1,
            "ended_at": 2,
            "window_end": 2,
            "updated_at": 2,
        }
    }
    state = repo.get_state("sync_forms_origin", "GAIA")
    assert state is not None
    assert state.checkpoint_synced_at == 555
    assert state.status == "COMPLETED"


def test_sync_state_repository_dynamo_set_state():
    repo = _make_repo()
    state = SyncState(
        job_name="sync_forms_origin",
        system="GAIA",
        checkpoint_synced_at=12345,
        status="RUNNING",
        execution_id="exec-2",
        started_at=10,
        ended_at=None,
        window_end=20,
        updated_at=10,
    )
    repo.set_state(state)

    assert len(repo.dynamo.put_calls) == 1
    item, pk, sk, _ = repo.dynamo.put_calls[0]
    assert item["checkpoint_synced_at"] == 12345
    assert item["status"] == "RUNNING"
    assert pk == "sync_state#sync_forms_origin#GAIA"
    assert sk == "METADATA"
