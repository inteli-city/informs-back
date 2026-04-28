from decimal import Decimal

from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource


class FakeTable:
    name = "fake-table"

    def __init__(self):
        self.update_item_kwargs = None

    def update_item(self, **kwargs):
        self.update_item_kwargs = kwargs
        return {"Attributes": {"ok": True}}


def _make_datasource():
    datasource = DynamoDatasource.__new__(DynamoDatasource)
    datasource.partition_key = "PK"
    datasource.sort_key = "SK"
    datasource.dynamo_table = FakeTable()
    return datasource


def test_update_item_builds_expression_and_condition():
    datasource = _make_datasource()
    condition_expression = object()

    response = datasource.update_item(
        partition_key="pk-1",
        sort_key="sk-1",
        update_dict={"status": "COMPLETED", "amount": 1.5},
        condition_expression=condition_expression,
    )

    kwargs = datasource.dynamo_table.update_item_kwargs
    assert response == {"Attributes": {"ok": True}}
    assert kwargs["Key"] == {"PK": "pk-1", "SK": "sk-1"}
    assert kwargs["UpdateExpression"] == "SET #attr0 = :val0, #attr1 = :val1"
    assert kwargs["ExpressionAttributeNames"] == {"#attr0": "status", "#attr1": "amount"}
    assert kwargs["ExpressionAttributeValues"] == {":val0": "COMPLETED", ":val1": Decimal("1.5")}
    assert kwargs["ConditionExpression"] is condition_expression
    assert kwargs["ReturnValues"] == "ALL_NEW"


def test_update_item_omits_empty_sort_key_and_condition():
    datasource = _make_datasource()

    datasource.update_item(
        partition_key="pk-1",
        sort_key=None,
        update_dict={"status": "PENDING"},
    )

    kwargs = datasource.dynamo_table.update_item_kwargs
    assert kwargs["Key"] == {"PK": "pk-1"}
    assert "ConditionExpression" not in kwargs
