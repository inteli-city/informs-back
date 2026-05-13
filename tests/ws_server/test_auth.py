"""Tests do Authenticator e do extract_token_from_headers.

Não testamos a verificação de assinatura JWT real — isso depende do JWKS
do Cognito e não agrega valor unitário (jose já é testado).  Testamos:
- extração de token dos headers (Authorization e Sec-WebSocket-Protocol)
- mapeamento role Profile → role tracking
- tratamento de profile inexistente / inativo / role desconhecida
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ws_server.auth import (
    AuthError,
    Authenticator,
    extract_token_from_headers,
)
from ws_server.config import Settings


_SETTINGS = Settings(
    stage="test",
    aws_region="sa-east-1",
    location_table="loc-test",
    profile_table="prof-test",
    cognito_user_pool_id="pool",
    cognito_app_client_id="client",
)


class TestExtractTokenFromHeaders:
    def test_authorization_bearer(self):
        assert extract_token_from_headers({"authorization": "Bearer abc.def"}) == "abc.def"

    def test_authorization_case_insensitive_value(self):
        # cabeçalho HTTP em si vem lowercase no FastAPI; o valor "Bearer" pode variar.
        assert extract_token_from_headers({"authorization": "bearer xyz"}) == "xyz"

    def test_sec_websocket_protocol_bearer_dot(self):
        assert (
            extract_token_from_headers({"sec-websocket-protocol": "Bearer.tok123"})
            == "tok123"
        )

    def test_sec_websocket_protocol_with_other_subprotocols(self):
        headers = {"sec-websocket-protocol": "chat, Bearer.tok123, json"}
        assert extract_token_from_headers(headers) == "tok123"

    def test_returns_none_when_absent(self):
        assert extract_token_from_headers({}) is None

    def test_returns_none_when_authorization_not_bearer(self):
        assert extract_token_from_headers({"authorization": "Basic Zm9v"}) is None


class TestAuthenticatorLookupRole:
    def _build(self, item: dict | None):
        ddb = MagicMock()
        ddb.Table.return_value.get_item.return_value = (
            {"Item": item} if item is not None else {}
        )
        return Authenticator(_SETTINGS, dynamodb_resource=ddb)

    def test_returns_role_when_active(self):
        auth = self._build({"role": "ADMIN", "active": True})
        assert auth._lookup_role("u1") == "ADMIN"

    def test_returns_role_when_active_field_absent(self):
        # Profile schema atual: `active` opcional, default = True
        auth = self._build({"role": "INSPECTOR"})
        assert auth._lookup_role("u1") == "INSPECTOR"

    def test_returns_none_when_inactive(self):
        auth = self._build({"role": "ADMIN", "active": False})
        assert auth._lookup_role("u1") is None

    def test_returns_none_when_not_found(self):
        auth = self._build(None)
        assert auth._lookup_role("u1") is None


class TestAuthenticatorAuthenticate:
    """Testa só o caminho pós-JWT, mockando _verify_jwt."""

    @pytest.mark.asyncio
    async def test_inspector_role_accepted(self, monkeypatch):
        ddb = MagicMock()
        ddb.Table.return_value.get_item.return_value = {
            "Item": {"role": "INSPECTOR", "active": True}
        }
        auth = Authenticator(_SETTINGS, dynamodb_resource=ddb)
        monkeypatch.setattr(auth, "_verify_jwt", AsyncMock(return_value={"sub": "u1"}))
        user = await auth.authenticate("dummy")
        assert user.user_id == "u1"
        assert user.role == "INSPECTOR"

    @pytest.mark.asyncio
    async def test_admin_role_accepted(self, monkeypatch):
        ddb = MagicMock()
        ddb.Table.return_value.get_item.return_value = {
            "Item": {"role": "ADMIN", "active": True}
        }
        auth = Authenticator(_SETTINGS, dynamodb_resource=ddb)
        monkeypatch.setattr(auth, "_verify_jwt", AsyncMock(return_value={"sub": "u2"}))
        user = await auth.authenticate("dummy")
        assert user.role == "ADMIN"

    @pytest.mark.asyncio
    async def test_missing_token_raises(self):
        auth = Authenticator(_SETTINGS, dynamodb_resource=MagicMock())
        with pytest.raises(AuthError, match="missing"):
            await auth.authenticate(None)

    @pytest.mark.asyncio
    async def test_token_without_sub_raises(self, monkeypatch):
        auth = Authenticator(_SETTINGS, dynamodb_resource=MagicMock())
        monkeypatch.setattr(auth, "_verify_jwt", AsyncMock(return_value={}))
        with pytest.raises(AuthError, match="sub"):
            await auth.authenticate("dummy")

    @pytest.mark.asyncio
    async def test_profile_not_found_raises(self, monkeypatch):
        ddb = MagicMock()
        ddb.Table.return_value.get_item.return_value = {}
        auth = Authenticator(_SETTINGS, dynamodb_resource=ddb)
        monkeypatch.setattr(auth, "_verify_jwt", AsyncMock(return_value={"sub": "ghost"}))
        with pytest.raises(AuthError, match="profile"):
            await auth.authenticate("dummy")

    @pytest.mark.asyncio
    async def test_unknown_role_raises(self, monkeypatch):
        ddb = MagicMock()
        ddb.Table.return_value.get_item.return_value = {
            "Item": {"role": "WHATEVER", "active": True}
        }
        auth = Authenticator(_SETTINGS, dynamodb_resource=ddb)
        monkeypatch.setattr(auth, "_verify_jwt", AsyncMock(return_value={"sub": "u1"}))
        with pytest.raises(AuthError, match="não autorizada"):
            await auth.authenticate("dummy")
