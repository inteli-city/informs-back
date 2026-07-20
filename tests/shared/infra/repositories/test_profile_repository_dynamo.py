import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound
from src.shared.infra.dtos.profile_dynamo_dto import ProfileDynamoDTO
from src.shared.infra.repositories.profile_repository_dynamo import ProfileRepositoryDynamo


USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"


class _ConditionalCheckFailed(Exception):
    pass


class _FakeClientExceptions:
    ConditionalCheckFailedException = _ConditionalCheckFailed


class _FakeMetaClient:
    exceptions = _FakeClientExceptions()


class _FakeMeta:
    client = _FakeMetaClient()


class _FakeTable:
    meta = _FakeMeta()


class FakeProfileDynamo:
    """Fake do DynamoDatasource para ProfileRepositoryDynamo (sem AWS)."""

    def __init__(self):
        self.dynamo_table = _FakeTable()
        self.get_item_response = {}
        self.put_should_conflict = False
        self.put_calls = []
        self.update_response = {}
        self.update_should_fail = False
        self.query_responses = []

    def get_item(self, partition_key, sort_key=None):
        return self.get_item_response

    def put_item(self, item, partition_key, sort_key=None, **kwargs):
        if self.put_should_conflict:
            raise _ConditionalCheckFailed("exists")
        self.put_calls.append((item, partition_key, sort_key, kwargs))
        return {"ok": True}

    def update_item(self, partition_key, sort_key, update_dict, condition_expression=None):
        if self.update_should_fail:
            raise _ConditionalCheckFailed("missing")
        return self.update_response

    def query(self, **kwargs):
        return self.query_responses.pop(0)


def _repo() -> ProfileRepositoryDynamo:
    repo = ProfileRepositoryDynamo.__new__(ProfileRepositoryDynamo)
    repo.dynamo = FakeProfileDynamo()
    return repo


def _profile(**overrides) -> Profile:
    base = dict(
        user_id=USER_ID,
        role=ProfileRole.ADMIN,
        name="Admin",
        email="admin@example.com",
        system="GAIA",
        active=True,
        created_at=1,
        updated_at=1,
        vehicle_plate=None,
    )
    base.update(overrides)
    return Profile(**base)


def _stored_item() -> dict:
    item = ProfileDynamoDTO.from_entity(_profile()).to_dynamo()
    item["PK"] = ProfileDynamoDTO.build_pk(USER_ID)
    item["SK"] = ProfileDynamoDTO.build_sk()
    return item


class TestProfileRepositoryDynamo:
    def test_get_by_user_id_found(self):
        repo = _repo()
        repo.dynamo.get_item_response = {"Item": _stored_item()}

        profile = repo.get_by_user_id(USER_ID)
        assert profile is not None
        assert profile.user_id == USER_ID
        assert profile.role == ProfileRole.ADMIN

    def test_get_by_user_id_not_found(self):
        repo = _repo()
        repo.dynamo.get_item_response = {}
        assert repo.get_by_user_id(USER_ID) is None

    def test_create_success(self):
        repo = _repo()
        profile = _profile()
        result = repo.create(profile)

        assert result.user_id == USER_ID
        item, pk, sk, kwargs = repo.dynamo.put_calls[0]
        assert pk == ProfileDynamoDTO.build_pk(USER_ID)
        assert sk == "METADATA"
        assert kwargs["ConditionExpression"] == "attribute_not_exists(PK)"

    def test_create_duplicate_raises(self):
        repo = _repo()
        repo.dynamo.put_should_conflict = True
        with pytest.raises(DuplicatedItem):
            repo.create(_profile())

    def test_soft_delete_success(self):
        repo = _repo()
        stored = _stored_item()
        stored["active"] = False
        stored["updated_at"] = 999
        repo.dynamo.update_response = {"Attributes": stored}

        profile = repo.soft_delete(USER_ID, updated_at=999)
        assert profile.active is False
        assert profile.updated_at == 999

    def test_soft_delete_conditional_failure_raises_not_found(self):
        repo = _repo()
        repo.dynamo.update_should_fail = True
        with pytest.raises(NoItemsFound):
            repo.soft_delete(USER_ID, updated_at=999)

    def test_soft_delete_without_attributes_raises_not_found(self):
        repo = _repo()
        repo.dynamo.update_response = {}
        with pytest.raises(NoItemsFound):
            repo.soft_delete(USER_ID, updated_at=999)

    def test_count_active_by_role_paginates(self):
        repo = _repo()
        repo.dynamo.query_responses = [
            {"Count": 2, "LastEvaluatedKey": {"PK": "x"}},
            {"Count": 3},
        ]
        assert repo.count_active_by_role(ProfileRole.ADMIN) == 5
