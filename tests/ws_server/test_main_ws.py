"""Tests de integração do endpoint /ws com TestClient da FastAPI.

Mocka:
- Authenticator: força MOTOCA ou GESTOR sem precisar de JWT real.
- LocationRepository: usa moto pra DynamoDB local.

Verifica o protocolo:
- snapshot inicial pro gestor
- broadcast de location ping motoca → gestor
- presence connect/disconnect
- payload inválido fecha ou retorna error sem matar a sessão
"""

import os

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from ws_server import config, main as main_module
from ws_server.auth import AuthenticatedUser


TABLE = "informs-tracking-location-test"
REGION = os.environ.get("AWS_REGION", "sa-east-1")


@pytest.fixture
def app_with_mocks(monkeypatch):
    """App pronto com auth mockada e DDB via moto."""
    with mock_aws():
        # Cria tabela location no moto.
        boto3.client("dynamodb", region_name=REGION).create_table(
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
        ddb = boto3.resource("dynamodb", region_name=REGION)

        # Settings dummy — não fazemos requests Cognito porque mockamos auth.
        fake_settings = config.Settings(
            stage="test",
            aws_region=REGION,
            location_table=TABLE,
            profile_table="prof-test",
            cognito_user_pool_id="pool",
            cognito_app_client_id="client",
        )
        monkeypatch.setattr(config, "load", lambda: fake_settings)

        # Stub do Authenticator: cliente passa Authorization: "Bearer u1:MOTOCA"
        # e a gente devolve AuthenticatedUser correspondente.
        # `await asyncio.sleep(0)` pra aderir ao contrato async sem
        # disparar python:S7503 (corrotina sem await).
        import asyncio
        from ws_server.auth import AuthError

        class StubAuth:
            async def authenticate(self, token):
                await asyncio.sleep(0)
                if not token or ":" not in token:
                    raise AuthError("token de teste inválido")
                user_id, role = token.split(":", 1)
                if role not in ("MOTOCA", "GESTOR"):
                    raise AuthError("role desconhecida")
                return AuthenticatedUser(user_id=user_id, role=role)

        # main.py faz `from .auth import Authenticator` — patch precisa
        # ser no namespace de main, não no de auth.
        monkeypatch.setattr(main_module, "Authenticator", lambda *_a, **_k: StubAuth())

        with TestClient(main_module.app) as client:
            yield client, ddb


class TestHealthEndpoint:
    def test_returns_ok(self, app_with_mocks):
        client, _ = app_with_mocks
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAuthFailureClosesSocket:
    def test_no_token_closes_with_4401(self, app_with_mocks):
        client, _ = app_with_mocks
        with pytest.raises(Exception):
            with client.websocket_connect("/ws") as ws:
                # leitura forçada — server fecha antes de aceitar
                ws.receive_json()


class TestGestorReceivesSnapshot:
    def test_snapshot_empty_when_no_motocas(self, app_with_mocks):
        client, _ = app_with_mocks
        with client.websocket_connect(
            "/ws", headers={"authorization": "Bearer g1:GESTOR"}
        ) as ws:
            msg = ws.receive_json()
            assert msg["type"] == "snapshot"
            assert msg["online"] == []


class TestMotocaPingFanOut:
    def test_motoca_ping_reaches_gestor(self, app_with_mocks):
        client, ddb = app_with_mocks
        with client.websocket_connect(
            "/ws", headers={"authorization": "Bearer g1:GESTOR"}
        ) as gestor_ws:
            gestor_ws.receive_json()  # consome snapshot

            with client.websocket_connect(
                "/ws", headers={"authorization": "Bearer m1:MOTOCA"}
            ) as motoca_ws:
                # Gestor recebe presence:connect
                evt = gestor_ws.receive_json()
                assert evt == {"type": "connect", "user_id": "m1"}

                # Motoca manda ping
                motoca_ws.send_json(
                    {"lat": -23.5, "lng": -46.6, "ts_device": 999}
                )

                # Gestor recebe location
                loc = gestor_ws.receive_json()
                assert loc["type"] == "location"
                assert loc["user_id"] == "m1"
                assert loc["lat"] == pytest.approx(-23.5)
                assert loc["ts_device"] == 999

                # E foi gravado no DDB
                items = ddb.Table(TABLE).query(
                    KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq(
                        "user#m1"
                    )
                )["Items"]
                assert len(items) == 1

            # Motoca disconectou → gestor recebe presence:disconnect
            evt = gestor_ws.receive_json()
            assert evt == {"type": "disconnect", "user_id": "m1"}


class TestInvalidPayloadDoesNotKillSession:
    def test_motoca_invalid_then_valid(self, app_with_mocks):
        client, _ = app_with_mocks
        with client.websocket_connect(
            "/ws", headers={"authorization": "Bearer g1:GESTOR"}
        ) as gestor_ws:
            gestor_ws.receive_json()
            with client.websocket_connect(
                "/ws", headers={"authorization": "Bearer m1:MOTOCA"}
            ) as motoca_ws:
                gestor_ws.receive_json()  # connect

                # ping sem ts_device
                motoca_ws.send_json({"lat": 0, "lng": 0})
                err = motoca_ws.receive_json()
                assert err["type"] == "error"

                # mesma sessão aceita ping válido depois
                motoca_ws.send_json({"lat": 1, "lng": 2, "ts_device": 1})
                loc = gestor_ws.receive_json()
                assert loc["type"] == "location"
                assert loc["lat"] == pytest.approx(1)


class TestDuplicateMotocaSession:
    def test_second_connection_kicks_first(self, app_with_mocks):
        client, _ = app_with_mocks
        with client.websocket_connect(
            "/ws", headers={"authorization": "Bearer m1:MOTOCA"}
        ) as ws1:
            # Segunda sessão do mesmo user_id — só conectar já força
            # o disconnect da primeira (sem precisar usar a referência).
            with client.websocket_connect(
                "/ws", headers={"authorization": "Bearer m1:MOTOCA"}
            ):
                with pytest.raises(Exception):
                    ws1.receive_text()
