"""Tests do Authenticator e do extract_token_from_headers.

Não testamos a verificação de assinatura JWT real — isso depende do JWKS
do Cognito e não agrega valor unitário (jose já é testado).  Testamos:
- extração de token dos headers (Authorization e Sec-WebSocket-Protocol)
- mapeamento RBAC do Profile (super admin, ADMIN, tracking.view/start) → modo do tracking
- fallback de profile inexistente para INSPECTOR
- tratamento de profile inativo / sem permissão de tracking
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


def _ddb(person: dict | None, memberships=(), roles=None):
    """Tabela fake: query devolve a partição da pessoa (METADATA + vínculos);
    get_item devolve o role do sistema pedido."""
    items = []
    if person is not None:
        items.append({"PK": "user#u1", "SK": "METADATA", **person})
    for system, role_id in memberships:
        items.append({"PK": "user#u1", "SK": f"system#{system}", "system": system, "role_id": role_id})
    roles = roles or {}

    def get_item(Key):
        role = roles.get((Key["PK"], Key["SK"]))
        return {"Item": role} if role is not None else {}

    ddb = MagicMock()
    ddb.Table.return_value.query.return_value = {"Items": items}
    ddb.Table.return_value.get_item.side_effect = get_item
    return ddb


def _role(system: str, role_id: str, actions: list) -> dict:
    return {("system#" + system, "role#" + role_id): {"actions": actions}}


class TestAuthenticatorLookupRole:
    def _build(self, *args, **kwargs):
        return Authenticator(_SETTINGS, dynamodb_resource=_ddb(*args, **kwargs))

    def test_super_admin_watches(self):
        assert self._build({"active": True, "super_admin": True})._lookup_role("u1") == "ADMIN"

    def test_system_admin_watches(self):
        auth = self._build({"active": True}, memberships=[("GAIA", "ADMIN")])
        assert auth._lookup_role("u1") == "ADMIN"

    def test_role_with_tracking_view_watches(self):
        auth = self._build(
            {"active": True}, memberships=[("GAIA", "r1")], roles=_role("GAIA", "r1", ["tracking.view"]),
        )
        assert auth._lookup_role("u1") == "ADMIN"

    def test_role_with_tracking_start_emits(self):
        auth = self._build(
            {"active": True}, memberships=[("GAIA", "r1")], roles=_role("GAIA", "r1", ["tracking.start"]),
        )
        assert auth._lookup_role("u1") == "INSPECTOR"

    def test_active_field_absent_counts_as_active(self):
        auth = self._build({}, memberships=[("GAIA", "r1")], roles=_role("GAIA", "r1", ["tracking.start"]))
        assert auth._lookup_role("u1") == "INSPECTOR"

    def test_role_without_tracking_actions_returns_none(self):
        auth = self._build(
            {"active": True}, memberships=[("GAIA", "r1")], roles=_role("GAIA", "r1", ["forms.assign"]),
        )
        assert auth._lookup_role("u1") is None

    def test_returns_none_when_inactive(self):
        assert self._build({"active": False, "super_admin": True})._lookup_role("u1") is None

    def test_returns_inspector_when_not_found(self):
        # Usuário comum autenticado no Cognito não precisa de Profile chumbado:
        # na ausência de Profile explícito, o WS trata como INSPECTOR.
        assert self._build(None)._lookup_role("u1") == "INSPECTOR"


class TestAuthenticatorAuthenticate:
    """Testa só o caminho pós-JWT, mockando _verify_jwt."""

    @staticmethod
    def _auth(monkeypatch, ddb, claims=None):
        auth = Authenticator(_SETTINGS, dynamodb_resource=ddb)
        monkeypatch.setattr(auth, "_verify_jwt", AsyncMock(return_value=claims or {"sub": "u1"}))
        return auth

    @pytest.mark.asyncio
    async def test_emitter_accepted(self, monkeypatch):
        ddb = _ddb({"active": True}, memberships=[("GAIA", "r1")], roles=_role("GAIA", "r1", ["tracking.start"]))
        user = await self._auth(monkeypatch, ddb).authenticate("dummy")
        assert user.user_id == "u1"
        assert user.role == "INSPECTOR"

    @pytest.mark.asyncio
    async def test_watcher_accepted(self, monkeypatch):
        ddb = _ddb({"active": True, "super_admin": True})
        user = await self._auth(monkeypatch, ddb).authenticate("dummy")
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
    async def test_profile_not_found_defaults_to_inspector(self, monkeypatch):
        user = await self._auth(monkeypatch, _ddb(None), {"sub": "ghost"}).authenticate("dummy")
        assert user.user_id == "ghost"
        assert user.role == "INSPECTOR"

    @pytest.mark.asyncio
    async def test_cognito_admin_claim_without_profile_still_defaults_to_inspector(self, monkeypatch):
        claims = {"sub": "u1", "custom:general_role": "ADMIN_COLLABORATOR"}
        user = await self._auth(monkeypatch, _ddb(None), claims).authenticate("dummy")
        assert user.role == "INSPECTOR"

    @pytest.mark.asyncio
    async def test_inactive_profile_raises(self, monkeypatch):
        auth = self._auth(monkeypatch, _ddb({"active": False, "super_admin": True}))
        with pytest.raises(AuthError, match="inativo"):
            await auth.authenticate("dummy")

    @pytest.mark.asyncio
    async def test_without_tracking_permission_raises(self, monkeypatch):
        ddb = _ddb({"active": True}, memberships=[("GAIA", "r1")], roles=_role("GAIA", "r1", ["forms.assign"]))
        with pytest.raises(AuthError, match="sem permissão de tracking"):
            await self._auth(monkeypatch, ddb).authenticate("dummy")
