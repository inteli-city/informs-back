import os
import sys

sys.path.append(os.getcwd())

from src.shared.domain.entities.sync_error_form import SyncErrorForm
from src.shared.infra.repositories.sync_error_form_repository_dynamo import SyncErrorFormRepositoryDynamo


class _FakeKeyExpr:
    pass


class _FakeKey:
    def __init__(self, name):
        self.name = name

    def eq(self, value):
        return _FakeKeyExpr()


class FakeSyncErrorFormDynamo:
    def __init__(self):
        self.partition_key = "PK"
        self.get_item_response = {}
        self.query_response = {"Items": []}
        self.put_calls = []
        self.delete_calls = []

    def put_item(self, item, partition_key, sort_key, is_decimal=False):
        self.put_calls.append((item, partition_key, sort_key, is_decimal))
        return {"ok": True}

    def query(self, key_condition_expression, **kwargs):
        return self.query_response

    def delete_item(self, partition_key, sort_key):
        self.delete_calls.append((partition_key, sort_key))
        return {"ok": True}


def _make_repo(monkeypatch):
    repo = SyncErrorFormRepositoryDynamo.__new__(SyncErrorFormRepositoryDynamo)
    repo.dynamo = FakeSyncErrorFormDynamo()
    monkeypatch.setattr("src.shared.infra.repositories.sync_error_form_repository_dynamo.Key", _FakeKey)
    return repo


def test_sync_error_form_repository_dynamo_upsert(monkeypatch):
    repo = _make_repo(monkeypatch)
    item = SyncErrorForm(
        job_name="sync_forms_origin",
        system="GAIA",
        form_id="form-1",
        source_updated_at=123,
        last_failed_at=999,
    )

    repo.upsert_error_form(item)

    assert len(repo.dynamo.put_calls) == 1
    data, pk, sk, _ = repo.dynamo.put_calls[0]
    assert data["form_id"] == "form-1"
    assert pk == "sync_error_form#sync_forms_origin#GAIA"
    assert sk == "form#form-1"


def test_sync_error_form_repository_dynamo_list_and_delete(monkeypatch):
    repo = _make_repo(monkeypatch)
    repo.dynamo.query_response = {
        "Items": [
            {
                "PK": "sync_error_form#sync_forms_origin#GAIA",
                "SK": "form#form-1",
                "form_id": "form-1",
                "source_updated_at": 123,
                "last_failed_at": 999,
            }
        ]
    }

    loaded = repo.list_error_forms("sync_forms_origin", "GAIA")
    assert len(loaded) == 1
    assert loaded[0].form_id == "form-1"

    repo.delete_error_forms("sync_forms_origin", "GAIA", ["form-1"])
    assert repo.dynamo.delete_calls == [(
        "sync_error_form#sync_forms_origin#GAIA",
        "form#form-1",
    )]
