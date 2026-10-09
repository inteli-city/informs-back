import os
import sys
from types import SimpleNamespace

import pytest

sys.path.append(os.getcwd())

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound
from src.shared.infra.dtos.profile_dynamo_dto import ProfileDynamoDTO
from src.shared.infra.dtos.system_membership_dynamo_dto import SystemMembershipDynamoDTO
from src.shared.infra.repositories.profile_repository_dynamo import ProfileRepositoryDynamo


USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"


class _ConditionalCheckFailed(Exception):
    pass


class FakeProfileDynamo:
    """Fake do DynamoDatasource para ProfileRepositoryDynamo (sem AWS)."""

    partition_key = "PK"
    sort_key = "SK"

    def __init__(self):
        # Espelha o caminho boto3 dynamo_table.meta.client.exceptions.<Name>.
        # SimpleNamespace evita declarar um campo com nome PascalCase (imposto
        # pela API do boto3, não renomeável).
        exceptions = SimpleNamespace(ConditionalCheckFailedException=_ConditionalCheckFailed)
        self.dynamo_table = SimpleNamespace(
            meta=SimpleNamespace(client=SimpleNamespace(exceptions=exceptions))
        )
        self.get_item_response = {}
        self.put_should_conflict = False
        self.put_calls = []
        self.delete_calls = []
        self.update_response = {}
        self.update_should_fail = False
        self.query_responses = []
        self.query_calls = []

    def get_item(self, partition_key, sort_key=None):
        return self.get_item_response

    def put_item(self, item, partition_key, sort_key=None, **kwargs):
        if self.put_should_conflict:
            raise _ConditionalCheckFailed("exists")
        self.put_calls.append((item, partition_key, sort_key, kwargs))
        return {"ok": True}

    def delete_item(self, partition_key, sort_key=None):
        self.delete_calls.append((partition_key, sort_key))
        return {}

    def update_item(self, partition_key, sort_key, update_dict, condition_expression=None):
        if self.update_should_fail:
            raise _ConditionalCheckFailed("missing")
        return self.update_response

    def query(self, **kwargs):
        self.query_calls.append(kwargs)
        return self.query_responses.pop(0)


def _repo() -> ProfileRepositoryDynamo:
    repo = ProfileRepositoryDynamo.__new__(ProfileRepositoryDynamo)
    repo.dynamo = FakeProfileDynamo()
    return repo


def _profile(**overrides) -> Profile:
    base = {
        "user_id": USER_ID,
        "name": "Admin",
        "email": "admin@example.com",
        "active": True,
        "created_at": 1,
        "updated_at": 1,
    }
    base.update(overrides)
    return Profile(**base)


def _stored_item() -> dict:
    item = ProfileDynamoDTO.from_entity(_profile()).to_dynamo()
    item["PK"] = ProfileDynamoDTO.build_pk(USER_ID)
    item["SK"] = ProfileDynamoDTO.build_sk()
    return item


def _membership_item(system="GAIA", role_id="r1") -> dict:
    return SystemMembershipDynamoDTO.from_entity(
        SystemMembership(user_id=USER_ID, system=system, role_id=role_id, created_at=1, updated_at=1)
    ).to_dynamo()


class TestProfileRepositoryDynamo:
    def test_get_by_user_id_found(self):
        repo = _repo()
        repo.dynamo.get_item_response = {"Item": _stored_item()}

        profile = repo.get_by_user_id(USER_ID)
        assert profile is not None
        assert profile.user_id == USER_ID
        assert profile.super_admin is False

    def test_get_by_user_id_not_found(self):
        repo = _repo()
        repo.dynamo.get_item_response = {}
        assert repo.get_by_user_id(USER_ID) is None

    def test_create_success(self):
        repo = _repo()
        profile = _profile()
        result = repo.create(profile)

        assert result.user_id == USER_ID
        _, pk, sk, kwargs = repo.dynamo.put_calls[0]
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

    def test_count_active_super_admins_paginates_on_the_index(self):
        repo = _repo()
        repo.dynamo.query_responses = [
            {"Count": 2, "LastEvaluatedKey": {"PK": "x"}},
            {"Count": 3},
        ]

        assert repo.count_active_super_admins() == 5
        assert repo.dynamo.query_calls[0]["IndexName"] == "ByRole"
        assert repo.dynamo.query_calls[0]["Select"] == "COUNT"
        assert repo.dynamo.query_calls[1]["ExclusiveStartKey"] == {"PK": "x"}

    def test_get_memberships_queries_the_person_partition(self):
        repo = _repo()
        repo.dynamo.query_responses = [{"Items": [_membership_item("GAIA"), _membership_item("SGC", "r2")]}]

        memberships = repo.get_memberships(USER_ID)

        assert [(m.system, m.role_id) for m in memberships] == [("GAIA", "r1"), ("SGC", "r2")]
        assert "IndexName" not in repo.dynamo.query_calls[0]

    def test_get_membership_not_found(self):
        repo = _repo()
        repo.dynamo.get_item_response = {}
        assert repo.get_membership(USER_ID, "GAIA") is None

    def test_put_membership_writes_the_index_keys(self):
        repo = _repo()
        repo.put_membership(SystemMembership(user_id=USER_ID, system="GAIA", role_id="r1", created_at=1, updated_at=1))

        item, pk, sk, _ = repo.dynamo.put_calls[0]
        assert (pk, sk) == (f"user#{USER_ID}", "system#GAIA")
        assert item["GSI1PK"] == "system#GAIA"
        assert item["GSI1SK"] == f"role#r1#user#{USER_ID}"

    def test_delete_membership(self):
        repo = _repo()
        repo.delete_membership(USER_ID, "GAIA")
        assert repo.dynamo.delete_calls == [(f"user#{USER_ID}", "system#GAIA")]

    def test_list_memberships_by_system_uses_the_index(self):
        repo = _repo()
        repo.dynamo.query_responses = [{"Items": [_membership_item("GAIA")]}]

        memberships = repo.list_memberships_by_system("GAIA")

        assert [m.user_id for m in memberships] == [USER_ID]
        assert repo.dynamo.query_calls[0]["IndexName"] == "ByRole"

    def test_count_memberships_by_role(self):
        repo = _repo()
        repo.dynamo.query_responses = [{"Count": 4}]
        assert repo.count_memberships_by_role("GAIA", "r1") == 4
