import os
import sys

import pytest
from botocore.exceptions import ClientError

sys.path.append(os.getcwd())

from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.helpers.functions.pagination_token import encode_pagination_token
from src.shared.infra.dtos.form_dynamo_dto import FormDynamoDTO
from src.shared.infra.repositories.form_repository_dynamo import FormRepositoryDynamo
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class FakeDynamoTable:
    def __init__(self, items):
        self.items = items
        self.scan_calls = []
        self.scan_responses = None

    def scan(self, **kwargs):
        self.scan_calls.append(kwargs)
        if self.scan_responses:
            return self.scan_responses.pop(0)
        return {"Items": self.items, "LastEvaluatedKey": None}


class FakeFormDynamo:
    def __init__(self, items):
        self.partition_key = "PK"
        self.sort_key = "SK"
        self.dynamo_table = FakeDynamoTable(items)
        self.put_calls = []
        self.get_item_response = {}
        self.query_kwargs = None
        self.query_calls = []
        self.query_response = {"Items": items, "LastEvaluatedKey": None}
        self.query_responses = None
        self.scan_items_kwargs = None
        self.scan_items_calls = []
        self.scan_items_response = {"Items": items, "LastEvaluatedKey": None}
        self.scan_items_responses = None
        self.update_response = {"Attributes": items[0]} if items else {}
        self.update_exception = None
        self.last_update = None

    def put_item(self, item, partition_key, sort_key, is_decimal=False):
        self.put_calls.append((item, partition_key, sort_key, is_decimal))
        return {"ok": True}

    def get_item(self, partition_key, sort_key):
        return self.get_item_response

    def query(self, **kwargs):
        self.query_kwargs = kwargs
        self.query_calls.append(kwargs)
        if self.query_responses:
            return self.query_responses.pop(0)
        return self.query_response

    def scan_items(self, filter_expression, **kwargs):
        self.scan_items_kwargs = {"filter_expression": filter_expression, **kwargs}
        self.scan_items_calls.append(self.scan_items_kwargs)
        if self.scan_items_responses:
            return self.scan_items_responses.pop(0)
        return self.scan_items_response

    def update_item(self, partition_key, sort_key, update_dict, condition_expression=None):
        if self.update_exception is not None:
            raise self.update_exception
        self.last_update = {
            "partition_key": partition_key,
            "sort_key": sort_key,
            "update_dict": update_dict,
            "condition_expression": condition_expression,
        }
        return self.update_response


def _make_repo_with_item():
    form = FormRepositoryMock().forms[0]
    item = FormDynamoDTO.from_entity(form).to_dynamo()
    item["PK"] = f"form#{form.id}"
    item["SK"] = "METADATA"
    repo = FormRepositoryDynamo.__new__(FormRepositoryDynamo)
    repo.dynamo = FakeFormDynamo([item])
    return repo, form, item


def test_form_repository_dynamo_get_form_by_id():
    repo, form, item = _make_repo_with_item()
    repo.dynamo.get_item_response = {"Item": item}
    fetched = repo.get_form_by_id(user_id=form.user_id, form_id=form.id)
    assert fetched.id == form.id

    repo.dynamo.get_item_response = {}
    assert repo.get_form_by_id(user_id=form.user_id, form_id=form.id) is None


def test_form_repository_dynamo_create_and_get_by_user():
    repo, form, item = _make_repo_with_item()
    repo.create_form(form)
    assert repo.dynamo.put_calls
    saved_item, pk, sk, _ = repo.dynamo.put_calls[0]
    assert saved_item["GSI1PK"] == f"user#{form.user_id}"
    assert "GSI1SK" in saved_item
    assert saved_item["GSI2PK"] == f"system#{form.system}"
    assert saved_item["GSI2SK"] == f"updated_at#{int(form.updated_at):013d}#form#{form.id}"
    assert pk == f"form#{form.id}"
    assert sk == "METADATA"

    repo.dynamo.query_response = {"Items": [item]}
    forms = repo.get_form_by_user_id(form.user_id)
    assert len(forms) == 1


def test_form_repository_dynamo_get_all_forms_query_path():
    repo, form, item = _make_repo_with_item()
    repo.dynamo.query_response = {
        "Items": [item],
        "LastEvaluatedKey": {"PK": "form#next", "SK": "METADATA"},
    }
    _ = encode_pagination_token({"PK": "form#start", "SK": "METADATA"})
    start_key = {"PK": "form#start", "SK": "METADATA"}

    forms, next_key = repo.get_all_forms(
        limit=1,
        exclusive_start_key=start_key,
        status=FormStatus.IN_PROGRESS,
        system="GAIA",
        user_id=form.user_id,
        created_at_start=1,
        created_at_end=10,
    )

    assert len(forms) == 1
    assert next_key is not None
    assert "FilterExpression" in repo.dynamo.query_kwargs
    assert "ExclusiveStartKey" in repo.dynamo.query_kwargs


def test_form_repository_dynamo_get_all_forms_keeps_querying_until_limit_after_filter():
    repo, form, item = _make_repo_with_item()
    repo.dynamo.query_responses = [
        {"Items": [], "LastEvaluatedKey": {"PK": "form#empty-page", "SK": "METADATA"}},
        {"Items": [item], "LastEvaluatedKey": None},
    ]

    forms, next_key = repo.get_all_forms(
        limit=1,
        status=FormStatus.IN_PROGRESS,
        system="GAIA",
        user_id=form.user_id,
    )

    assert len(forms) == 1
    assert next_key is None
    assert len(repo.dynamo.query_calls) == 2
    assert repo.dynamo.query_calls[1]["ExclusiveStartKey"] == {"PK": "form#empty-page", "SK": "METADATA"}


def test_form_repository_dynamo_get_all_forms_search_reads_all_pages_and_does_not_return_cursor():
    repo, form, item = _make_repo_with_item()
    other_item = dict(item)
    other_item["PK"] = "form#d61dbf66-a10f-11ed-a8fc-0242ac120099"
    other_item["form_title"] = "Unrelated"
    matched_item = dict(item)
    matched_item["PK"] = "form#d61dbf66-a10f-11ed-a8fc-0242ac120098"
    matched_item["form_title"] = "Inspection target"
    repo.dynamo.query_responses = [
        {"Items": [other_item], "LastEvaluatedKey": {"PK": "form#page-2", "SK": "METADATA"}},
        {"Items": [matched_item], "LastEvaluatedKey": None},
    ]

    forms, next_key = repo.get_all_forms(
        limit=1,
        system="GAIA",
        user_id=form.user_id,
        search="target",
    )

    assert [form.form_title for form in forms] == ["Inspection target"]
    assert next_key is None
    assert len(repo.dynamo.query_calls) == 2
    assert all("Limit" not in call for call in repo.dynamo.query_calls)


def test_form_repository_dynamo_get_all_forms_scan_path():
    repo, _, item = _make_repo_with_item()
    repo.dynamo.dynamo_table.items = [item]

    forms, next_key = repo.get_all_forms(limit=10)

    assert len(forms) == 1
    assert next_key is None
    assert repo.dynamo.dynamo_table.scan_calls


def test_form_repository_dynamo_update_and_cancel():
    repo, form, item = _make_repo_with_item()
    repo.dynamo.update_response = {"Attributes": item}
    repo.dynamo.get_item_response = {"Item": item}

    updated = repo.update_form(
        user_id=form.user_id,
        form_id=form.id,
        status=FormStatus.COMPLETED,
        updated_at=123,
        sections=form.sections,
        justification=form.justification,
    )
    assert updated is not None
    assert "status" in repo.dynamo.last_update["update_dict"]
    assert "sections" in repo.dynamo.last_update["update_dict"]
    assert "justification" in repo.dynamo.last_update["update_dict"]
    assert "GSI2PK" in repo.dynamo.last_update["update_dict"]
    assert "GSI2SK" in repo.dynamo.last_update["update_dict"]

    cancelled = repo.update_form(
        user_id=form.user_id,
        form_id=form.id,
        status=FormStatus.CANCELLED,
        justification=form.justification,
        cancelled_at=1,
        updated_at=2,
    )
    assert cancelled is not None


def test_form_repository_dynamo_update_uses_expected_status_condition():
    repo, form, item = _make_repo_with_item()
    repo.dynamo.update_response = {"Attributes": item}
    repo.dynamo.get_item_response = {"Item": item}

    repo.update_form(
        user_id=form.user_id,
        form_id=form.id,
        status=FormStatus.COMPLETED,
        updated_at=123,
        expected_status=FormStatus.IN_PROGRESS,
    )

    assert repo.dynamo.last_update["condition_expression"] is not None


def test_form_repository_dynamo_update_maps_conditional_check_failure():
    repo, form, item = _make_repo_with_item()
    repo.dynamo.get_item_response = {"Item": item}
    repo.dynamo.update_exception = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "failed"}},
        "UpdateItem",
    )

    with pytest.raises(ForbiddenAction):
        repo.update_form(
            user_id=form.user_id,
            form_id=form.id,
            status=FormStatus.COMPLETED,
            updated_at=123,
            expected_status=FormStatus.IN_PROGRESS,
        )


def test_form_repository_dynamo_update_reraises_unknown_client_error():
    repo, form, item = _make_repo_with_item()
    repo.dynamo.get_item_response = {"Item": item}
    repo.dynamo.update_exception = ClientError(
        {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "retry"}},
        "UpdateItem",
    )

    with pytest.raises(ClientError):
        repo.update_form(
            user_id=form.user_id,
            form_id=form.id,
            status=FormStatus.COMPLETED,
            updated_at=123,
            expected_status=FormStatus.IN_PROGRESS,
        )


def test_form_repository_dynamo_update_without_attributes():
    repo, form, _ = _make_repo_with_item()
    repo.dynamo.update_response = {}
    updated = repo.update_form(
        user_id=form.user_id,
        form_id=form.id,
        status=FormStatus.COMPLETED,
        updated_at=123,
    )
    assert updated is None


def test_form_repository_dynamo_get_forms_updated_since():
    repo, form, item = _make_repo_with_item()
    repo.dynamo.query_response = {"Items": [item], "LastEvaluatedKey": None}

    forms, next_key = repo.get_forms_updated_since(
        system=form.system,
        updated_at_start=1,
        updated_at_end=9999999999999,
        limit=10,
        status=[FormStatus.COMPLETED, FormStatus.SENT],
    )

    assert len(forms) == 1
    assert next_key is None
    assert repo.dynamo.query_kwargs["IndexName"] == "SystemUpdatedAtIndex"
    assert repo.dynamo.query_kwargs["ScanIndexForward"] is True
    assert "FilterExpression" in repo.dynamo.query_kwargs
