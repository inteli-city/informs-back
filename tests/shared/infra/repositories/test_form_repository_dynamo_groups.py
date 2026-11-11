"""Grupos na persistência do formulário e no filtro do pool (ADR-0022)."""

import pytest

from src.shared.domain.entities.system_group import SystemGroup
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.infra.dtos.form_dynamo_dto import FormDynamoDTO
from src.shared.infra.dtos.system_group_dynamo_dto import SystemGroupDynamoDTO
from src.shared.infra.dtos.system_membership_dynamo_dto import SystemMembershipDynamoDTO
from src.shared.infra.repositories.form_repository_dynamo import FormRepositoryDynamo
from tests.modules.test_groups_scenario import _form
from tests.shared.infra.repositories.test_form_repository_dynamo import FakeFormDynamo

FORM_ID = "20000000-0000-4000-8000-000000000001"


def _item(form):
    item = FormDynamoDTO.from_entity(form).to_dynamo()
    item["PK"] = f"form#{form.id}"
    item["SK"] = "METADATA"
    return item


def _repo(items=None):
    repo = FormRepositoryDynamo.__new__(FormRepositoryDynamo)
    repo.dynamo = FakeFormDynamo(items or [])
    return repo


class TestFormGroupsDto:
    def test_groups_round_trip(self):
        item = _item(_form(FORM_ID, groups=["equipe-a", "equipe-b"]))

        assert item["groups"] == ["equipe-a", "equipe-b"]
        assert FormDynamoDTO.from_dynamo(item).to_entity().groups == ["equipe-a", "equipe-b"]

    def test_without_groups_the_attribute_is_absent(self):
        # O filtro do pool trata "sem grupos" como attribute_not_exists(groups).
        item = _item(_form(FORM_ID))

        assert "groups" not in item
        assert FormDynamoDTO.from_dynamo(item).to_entity().groups == []

    def test_create_form_writes_groups_on_the_pool_item(self):
        repo = _repo()
        repo.create_form(_form(FORM_ID, groups=["equipe-a"]))

        saved_item = repo.dynamo.put_calls[0][0]
        assert saved_item["groups"] == ["equipe-a"]
        assert saved_item["GSI3PK"] == "pool#UBERLANDIA"


class TestPoolGroupsFilter:
    def test_without_groups_argument_there_is_no_filter(self):
        repo = _repo()
        repo.get_pool_forms(system="UBERLANDIA", limit=10)

        assert "FilterExpression" not in repo.dynamo.query_kwargs

    def test_filter_accepts_ungrouped_and_each_group_of_the_requester(self):
        repo = _repo()
        repo.get_pool_forms(system="UBERLANDIA", limit=10, groups=["equipe-a", "equipe-b"])

        expression = repo.dynamo.query_kwargs["FilterExpression"]
        assert repo.dynamo.query_kwargs["IndexName"] == "PoolIndex"
        assert expression.get_expression()["format"] == "({0} {operator} {1})"
        assert "attribute_not_exists" in str(_flatten(expression))
        assert {"equipe-a", "equipe-b"} <= set(_values(expression))

    def test_requester_without_groups_only_sees_ungrouped(self):
        repo = _repo()
        repo.get_pool_forms(system="UBERLANDIA", limit=10, groups=[])

        expression = repo.dynamo.query_kwargs["FilterExpression"]
        assert expression.get_expression()["operator"] == "attribute_not_exists"

    def test_pool_has_group_counts_with_a_filter(self):
        repo = _repo()
        repo.dynamo.query_response = {"Count": 1, "Items": [], "LastEvaluatedKey": None}

        assert repo.pool_has_group("UBERLANDIA", "equipe-a") is True
        assert repo.dynamo.query_kwargs["Select"] == "COUNT"

    def test_pool_has_group_walks_the_pages(self):
        repo = _repo()
        repo.dynamo.query_responses = [
            {"Count": 0, "LastEvaluatedKey": {"PK": "x"}},
            {"Count": 0, "LastEvaluatedKey": None},
        ]

        assert repo.pool_has_group("UBERLANDIA", "equipe-a") is False
        assert len(repo.dynamo.query_calls) == 2


class TestGroupEntities:
    def test_membership_groups_round_trip(self):
        membership = SystemMembership(user_id="u", system="GAIA", role_id="r", created_at=1, updated_at=1,
                                      groups=["equipe-a", "equipe-a"])
        item = SystemMembershipDynamoDTO.from_entity(membership).to_dynamo()

        assert membership.groups == ["equipe-a"]
        assert SystemMembershipDynamoDTO.from_dynamo(item).to_entity().groups == ["equipe-a"]

    def test_membership_saved_before_groups_reads_as_empty(self):
        item = {"user_id": "u", "system": "GAIA", "role_id": "r", "created_at": 1, "updated_at": 1}
        assert SystemMembershipDynamoDTO.from_dynamo(item).to_entity().groups == []

    def test_group_round_trip(self):
        group = SystemGroup(system="GAIA", group_id="equipe-leste", name=" Equipe Leste ", created_at=1, updated_at=2)
        item = SystemGroupDynamoDTO.from_entity(group).to_dynamo()

        assert SystemGroupDynamoDTO.build_sk("equipe-leste") == "group#equipe-leste"
        assert SystemGroupDynamoDTO.from_dynamo(item).to_entity().name == "Equipe Leste"

    @pytest.mark.parametrize("group_id", ["Equipe", "equipe_a", "-a", "a-", "", "a" * 41])
    def test_invalid_group_id(self, group_id):
        with pytest.raises(EntityError):
            SystemGroup(system="GAIA", group_id=group_id, name="Equipe", created_at=1, updated_at=1)

    def test_form_rejects_blank_group(self):
        with pytest.raises(EntityError):
            _form(FORM_ID, groups=[" "])

    def test_form_open_to_groups(self):
        assert _form(FORM_ID).is_open_to_groups([]) is True
        assert _form(FORM_ID, groups=["equipe-a"]).is_open_to_groups(["equipe-b", "equipe-a"]) is True
        assert _form(FORM_ID, groups=["equipe-a"]).is_open_to_groups(["equipe-b"]) is False


def _flatten(expression):
    """Operadores da árvore de condições do boto3."""
    out = [expression.get_expression()["operator"]]
    for value in expression.get_expression()["values"]:
        if hasattr(value, "get_expression"):
            out.extend(_flatten(value))
    return out


def _values(expression):
    """Valores literais da árvore de condições do boto3."""
    out = []
    for value in expression.get_expression()["values"]:
        if hasattr(value, "get_expression"):
            out.extend(_values(value))
        elif isinstance(value, str):
            out.append(value)
    return out
