import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.helpers.functions.pagination_token import encode_pagination_token
from src.shared.infra.dtos.template_dynamo_dto import TemplateDynamoDTO
from src.shared.infra.repositories.template_repository_dynamo import TemplateRepositoryDynamo


class FakeTemplateDynamo:
    def __init__(self):
        self.put_calls = []
        self.get_item_response = {}
        self.query_kwargs = None
        self.query_response = {"Items": [], "LastEvaluatedKey": None}
        self.transact_items = None

    def put_item(self, item, partition_key, sort_key):
        self.put_calls.append((item, partition_key, sort_key))
        return {"ok": True}

    def get_item(self, partition_key, sort_key):
        return self.get_item_response

    def query(self, **kwargs):
        self.query_kwargs = kwargs
        return self.query_response

    def build_transaction_item_delete(self, partition_key, sort_key=None):
        return {"Delete": {"PK": partition_key, "SK": sort_key}}

    def build_transaction_item_put(self, item, partition_key, sort_key=None):
        return {"Put": {"Item": item, "PK": partition_key, "SK": sort_key}}

    def transact_write_items(self, transact_items):
        self.transact_items = transact_items
        return {"ok": True}


def _make_template():
    section = Section(section_id=1, fields=[TextField(label="Field", required=True, key="k", order=1)])
    return Template(
        id="12345678-1234-1234-1234-123456789012",
        name="Template",
        system="GAIA",
        created_by="user-1",
        sections=[section],
        created_at=1,
        updated_at=2,
        is_active=True,
        description="desc",
    )


def test_template_repository_dynamo_create_and_get():
    repo = TemplateRepositoryDynamo.__new__(TemplateRepositoryDynamo)
    repo.dynamo = FakeTemplateDynamo()
    template = _make_template()

    repo.create_template(template)
    assert repo.dynamo.put_calls
    item, partition_key, sort_key = repo.dynamo.put_calls[0]
    assert item["GSI1PK"] == "system#GAIA"
    assert "GSI1SK" in item
    assert partition_key == f"template#{template.id}"
    assert sort_key == "METADATA"

    repo.dynamo.get_item_response = {"Item": TemplateDynamoDTO.from_entity(template).to_dynamo()}
    fetched = repo.get_template(template.id)
    assert fetched.id == template.id

    repo.dynamo.get_item_response = {}
    assert repo.get_template(template.id) is None


def test_template_repository_dynamo_get_all_and_update():
    repo = TemplateRepositoryDynamo.__new__(TemplateRepositoryDynamo)
    repo.dynamo = FakeTemplateDynamo()
    template = _make_template()

    item = TemplateDynamoDTO.from_entity(template).to_dynamo()
    repo.dynamo.query_response = {
        "Items": [item],
        "LastEvaluatedKey": {"PK": "template#next", "SK": "METADATA"},
    }
    token = encode_pagination_token({"PK": "template#start", "SK": "METADATA"})

    results, next_key = repo.get_all_templates(
        system="GAIA",
        limit=10,
        exclusive_start_key=token,
        name_contains="Tem",
        is_active=True,
    )

    assert len(results) == 1
    assert next_key is not None
    assert "FilterExpression" in repo.dynamo.query_kwargs
    assert "ExclusiveStartKey" in repo.dynamo.query_kwargs

    updated = repo.update_template(template)
    assert updated.id == template.id
    assert repo.dynamo.transact_items is not None
    assert len(repo.dynamo.transact_items) == 2
