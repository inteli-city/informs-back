"""Tests do LocationRepository com moto (DynamoDB local em memória)."""

import os

import boto3
import pytest
from moto import mock_aws

from ws_server.location_repo import LocationRepository


TABLE = "formularios-tracking-location-test"
# Region puxa de env (cai pra default só quando rodando local sem AWS_REGION).
# Resolve python:S6262 — Sonar não gosta de region literal hardcoded.
REGION = os.environ.get("AWS_REGION", "sa-east-1")


@pytest.fixture
def ddb():
    with mock_aws():
        client = boto3.client("dynamodb", region_name=REGION)
        client.create_table(
            TableName=TABLE,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield boto3.resource("dynamodb", region_name=REGION)


class TestLocationRepository:
    def test_put_ping_minimal(self, ddb):
        repo = LocationRepository(table_name=TABLE, region=REGION, dynamodb_resource=ddb)
        repo.put_ping(
            user_id="u1", lat=-23.5, lng=-46.6, ts_server=1000, ts_device=999
        )
        item = ddb.Table(TABLE).get_item(
            Key={"PK": "user#u1", "SK": "ts#1000"}
        )["Item"]
        assert float(item["lat"]) == pytest.approx(-23.5)
        assert float(item["lng"]) == pytest.approx(-46.6)
        assert int(item["ts_device"]) == 999
        assert "accuracy" not in item

    def test_put_ping_with_accuracy(self, ddb):
        repo = LocationRepository(table_name=TABLE, region=REGION, dynamodb_resource=ddb)
        repo.put_ping(
            user_id="u1",
            lat=0,
            lng=0,
            ts_server=2000,
            ts_device=1500,
            accuracy=5.0,
        )
        item = ddb.Table(TABLE).get_item(
            Key={"PK": "user#u1", "SK": "ts#2000"}
        )["Item"]
        assert float(item["accuracy"]) == pytest.approx(5.0)

    def test_writes_are_independent(self, ddb):
        # Multiplos pings do mesmo user com ts_server diferente coexistem.
        repo = LocationRepository(table_name=TABLE, region=REGION, dynamodb_resource=ddb)
        for ts in (1000, 2000, 3000):
            repo.put_ping(user_id="u1", lat=0, lng=0, ts_server=ts, ts_device=ts)

        resp = ddb.Table(TABLE).query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq("user#u1")
        )
        assert resp["Count"] == 3

    def test_query_history_returns_range_in_order(self, ddb):
        repo = LocationRepository(table_name=TABLE, region=REGION, dynamodb_resource=ddb)
        # Insere 5 pings em ordem cronológica.
        for ts in (1000, 2000, 3000, 4000, 5000):
            repo.put_ping(
                user_id="u1", lat=ts / 1000, lng=ts / 2000,
                ts_server=ts, ts_device=ts - 50,
            )
        # Insere ping de OUTRO user pra confirmar que filter por PK funciona.
        repo.put_ping(user_id="u2", lat=99, lng=99, ts_server=2500, ts_device=2400)

        items = repo.query_history(user_id="u1", since_ms=2000, until_ms=4000)
        assert [i["ts"] for i in items] == [2000, 3000, 4000]
        assert items[0]["lat"] == pytest.approx(2.0)
        assert items[0]["ts_device"] == 1950
        assert items[0]["accuracy"] is None

    def test_query_history_includes_accuracy(self, ddb):
        repo = LocationRepository(table_name=TABLE, region=REGION, dynamodb_resource=ddb)
        repo.put_ping(
            user_id="u1", lat=0, lng=0, ts_server=1000, ts_device=999, accuracy=7.5,
        )
        items = repo.query_history(user_id="u1", since_ms=0, until_ms=2000)
        assert items[0]["accuracy"] == pytest.approx(7.5)

    def test_query_history_empty_when_out_of_range(self, ddb):
        repo = LocationRepository(table_name=TABLE, region=REGION, dynamodb_resource=ddb)
        repo.put_ping(user_id="u1", lat=0, lng=0, ts_server=1000, ts_device=999)
        assert repo.query_history(user_id="u1", since_ms=2000, until_ms=3000) == []
        assert repo.query_history(user_id="ghost", since_ms=0, until_ms=9999) == []
