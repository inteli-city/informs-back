import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.shared.infra.repositories.location_repository_dynamo import LocationRepositoryDynamo


USER_ID = "fake-inspector-id"


class FakeLocationDynamo:
    """Fake do DynamoDatasource para LocationRepositoryDynamo (sem AWS)."""

    def __init__(self):
        self.partition_key = "PK"
        self.sort_key = "SK"
        self.query_responses = []
        self.query_calls = []

    def query(self, key_condition_expression=None, **kwargs):
        self.query_calls.append(kwargs)
        return self.query_responses.pop(0)


def _repo() -> LocationRepositoryDynamo:
    repo = LocationRepositoryDynamo.__new__(LocationRepositoryDynamo)
    repo.dynamo = FakeLocationDynamo()
    return repo


def _item(ts_ms: int, accuracy=5.0) -> dict:
    item = {
        "PK": f"user#{USER_ID}",
        "SK": f"ts#{ts_ms}",
        "lat": -23.55,
        "lng": -46.63,
        "ts_device": ts_ms - 50,
    }
    if accuracy is not None:
        item["accuracy"] = accuracy
    return item


class TestLocationRepositoryDynamo:
    def test_query_history_maps_items(self):
        repo = _repo()
        repo.dynamo.query_responses = [{"Items": [_item(1000), _item(2000)]}]

        pings = repo.query_history(user_id=USER_ID, since_ms=0, until_ms=10_000)

        assert len(pings) == 2
        assert pings[0].user_id == USER_ID
        assert pings[0].ts == 1000
        assert pings[0].ts_device == 950
        assert pings[0].accuracy == pytest.approx(5.0)

    def test_query_history_paginates(self):
        repo = _repo()
        repo.dynamo.query_responses = [
            {"Items": [_item(1000)], "LastEvaluatedKey": {"PK": "x", "SK": "ts#1000"}},
            {"Items": [_item(2000)]},
        ]

        pings = repo.query_history(user_id=USER_ID, since_ms=0, until_ms=10_000)

        assert [p.ts for p in pings] == [1000, 2000]
        # segunda query recebeu o cursor da primeira
        assert repo.dynamo.query_calls[1]["ExclusiveStartKey"] == {"PK": "x", "SK": "ts#1000"}

    def test_query_history_accuracy_absent_becomes_none(self):
        repo = _repo()
        repo.dynamo.query_responses = [{"Items": [_item(1000, accuracy=None)]}]

        pings = repo.query_history(user_id=USER_ID, since_ms=0, until_ms=10_000)
        assert pings[0].accuracy is None

    def test_query_history_empty(self):
        repo = _repo()
        repo.dynamo.query_responses = [{"Items": []}]
        assert repo.query_history(user_id=USER_ID, since_ms=0, until_ms=10_000) == []
