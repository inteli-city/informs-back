from decimal import Decimal

from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource


class FakeTable:
    name = "fake-table"

    def __init__(self):
        self.update_item_kwargs = None
        self.put_item_kwargs = None

    def update_item(self, **kwargs):
        self.update_item_kwargs = kwargs
        return {"Attributes": {"ok": True}}

    def put_item(self, **kwargs):
        self.put_item_kwargs = kwargs
        return {}


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


def test_put_item_forwards_condition_expression():
    datasource = _make_datasource()

    datasource.put_item(
        item={"foo": "bar"},
        partition_key="pk-1",
        sort_key="sk-1",
        ConditionExpression="attribute_not_exists(PK)",
    )

    kwargs = datasource.dynamo_table.put_item_kwargs
    assert kwargs["ConditionExpression"] == "attribute_not_exists(PK)"
    assert kwargs["Item"] == {"foo": "bar", "PK": "pk-1", "SK": "sk-1"}


def test_put_item_without_extra_kwargs_still_works():
    datasource = _make_datasource()

    datasource.put_item(item={"foo": "bar"}, partition_key="pk-1", sort_key="sk-1")

    kwargs = datasource.dynamo_table.put_item_kwargs
    assert kwargs == {"Item": {"foo": "bar", "PK": "pk-1", "SK": "sk-1"}}


def test_put_item_is_decimal_kwarg_not_forwarded_to_boto():
    datasource = _make_datasource()

    datasource.put_item(item={"amount": 1.5}, partition_key="pk-1", sort_key="sk-1", is_decimal=True)

    kwargs = datasource.dynamo_table.put_item_kwargs
    assert kwargs == {"Item": {"amount": 1.5, "PK": "pk-1", "SK": "sk-1"}}
    assert "is_decimal" not in kwargs
