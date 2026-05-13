"""Autenticação no handshake do WS.

Fluxo:
1. Cliente conecta com header `Authorization: Bearer <id_token Cognito>`
   (ou `Sec-WebSocket-Protocol: Bearer.<token>` como fallback — alguns
   clientes browser não conseguem injetar Authorization em WS).
2. Validamos a assinatura do JWT contra o JWKS do User Pool (cacheado).
3. Extraímos `sub` (user_id) e buscamos role na tabela
   `informs-tracking-profile-{stage}`.
4. Mapeamos role aplicacional → papel do tracking:
       INSPECTOR → MOTOCA
       ADMIN     → GESTOR
   (decisão consciente: reusa enum existente sem migração de dados;
   documentado no ADR/README do tracking.)

Erros levantam `AuthError` que o caller transforma em close(code=4401).
"""

from dataclasses import dataclass
from typing import Literal, Optional

import boto3
import httpx
from jose import jwt
from jose.exceptions import JWTError

from .config import Settings


TrackingRole = Literal["MOTOCA", "GESTOR"]

_PROFILE_TO_TRACKING: dict[str, TrackingRole] = {
    "INSPECTOR": "MOTOCA",
    "ADMIN": "GESTOR",
}


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    role: TrackingRole


class AuthError(Exception):
    """Levantada quando o handshake falha (JWT inválido, role ausente, etc)."""


class Authenticator:
    """Stateful: cacheia JWKS e a tabela de profile."""

    def __init__(self, settings: Settings, dynamodb_resource=None) -> None:
        self._settings = settings
        self._jwks: Optional[dict] = None
        self._dynamodb = dynamodb_resource or boto3.resource(
            "dynamodb", region_name=settings.aws_region
        )

    async def authenticate(self, token: Optional[str]) -> AuthenticatedUser:
        if not token:
            raise AuthError("missing token")

        claims = await self._verify_jwt(token)
        user_id = claims.get("sub")
        if not user_id:
            raise AuthError("token sem sub")

        role = self._lookup_role(user_id)
        if role is None:
            raise AuthError(f"profile não encontrado pra user {user_id}")

        tracking_role = _PROFILE_TO_TRACKING.get(role)
        if tracking_role is None:
            raise AuthError(f"role {role!r} não autorizada no tracking")

        return AuthenticatedUser(user_id=user_id, role=tracking_role)

    async def _verify_jwt(self, token: str) -> dict:
        if self._jwks is None:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(self._settings.cognito_jwks_url)
                resp.raise_for_status()
                self._jwks = resp.json()

        # Lemos o header sem verificar APENAS pra descobrir o `kid` (id da
        # chave do JWKS) e o `alg`. A verificação real de assinatura,
        # audience, issuer e expiration é feita em jwt.decode() abaixo,
        # que SÓ retorna se tudo for válido. Este uso é o padrão
        # recomendado pelo próprio python-jose pra fluxo com JWKS.
        # NOSONAR: python:S5659 — assinatura é validada em jwt.decode().
        unverified_header = _read_unverified_header(token)
        kid = unverified_header.get("kid")
        alg = unverified_header.get("alg", "RS256")

        key = next(
            (k for k in self._jwks.get("keys", []) if k.get("kid") == kid), None
        )
        if key is None:
            raise AuthError("kid do token não bate com nenhuma chave do JWKS")

        try:
            # Esta chamada valida assinatura (RS256 contra a chave pública),
            # audience (client_id), issuer e expiração. Levanta JWTError
            # se qualquer uma falhar.
            return jwt.decode(
                token,
                key,
                algorithms=[alg],
                audience=self._settings.cognito_app_client_id,
                issuer=self._settings.cognito_issuer,
                options={"verify_at_hash": False},
            )
        except JWTError as exc:
            raise AuthError(f"validação JWT falhou: {exc}") from exc

    def _lookup_role(self, user_id: str) -> Optional[str]:
        """Lê role do Profile no DynamoDB. Convenção do schema:

        PK = user#{user_id}
        SK = METADATA
        attrs = {role: 'ADMIN'|'INSPECTOR', active: bool, ...}

        Retorna None se profile não existe ou está inativo.
        """
        table = self._dynamodb.Table(self._settings.profile_table)
        resp = table.get_item(Key={"PK": f"user#{user_id}", "SK": "METADATA"})
        item = resp.get("Item")
        if not item or not item.get("active", True):
            return None
        return item.get("role")


def extract_token_from_headers(headers: dict[str, str]) -> Optional[str]:
    """Aceita Authorization: Bearer X ou Sec-WebSocket-Protocol: Bearer.X.

    O segundo formato é a saída do hack padrão pra WS em browser (que não
    deixa setar headers customizados na API nativa). Cliente passa
    `["Bearer.<token>"]` como subprotocolo; aqui a gente extrai.
    """
    auth = headers.get("authorization") or headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()

    proto = headers.get("sec-websocket-protocol") or headers.get(
        "Sec-WebSocket-Protocol"
    )
    if proto:
        for part in (p.strip() for p in proto.split(",")):
            if part.startswith("Bearer."):
                return part[len("Bearer.") :]

    return None


def _read_unverified_header(token: str) -> dict:
    """Lê o header do JWT SEM validar assinatura.

    Uso EXCLUSIVO: descobrir `kid` e `alg` pra escolher a chave pública
    correta no JWKS. A validação real acontece em `jwt.decode()` no caller,
    que verifica assinatura, audience, issuer e expiration. Padrão
    documentado pelo próprio python-jose pra fluxo Cognito/Auth0.
    """
    try:
        return jwt.get_unverified_header(token)  # NOSONAR: ver docstring
    except JWTError as exc:
        raise AuthError(f"header JWT inválido: {exc}") from exc
