"""Config lido das env vars (setadas pelo systemd EnvironmentFile)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    stage: str  # "dev" | "homolog" | "prod"
    aws_region: str
    # Nomes físicos auto-gerados pelo CFN. Injetados pelo deploy script
    # (scripts/deploy_ws_server.sh) via cloudformation describe-stacks:
    #   LOCATION_TABLE → FormulariosTrackingStack:LocationTableName_{stage}
    #   PROFILE_TABLE  → FormulariosStack{stage}:ProfileTableName
    location_table: str
    profile_table: str
    cognito_user_pool_id: str
    cognito_app_client_id: str  # validado contra o claim aud/client_id

    @property
    def cognito_jwks_url(self) -> str:
        return (
            f"https://cognito-idp.{self.aws_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}/.well-known/jwks.json"
        )

    @property
    def cognito_issuer(self) -> str:
        return (
            f"https://cognito-idp.{self.aws_region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}"
        )


def load() -> Settings:
    """Carrega settings do environment. Falha cedo se variáveis essenciais faltam."""
    return Settings(
        stage=_required("STAGE"),
        aws_region=_required("AWS_REGION"),
        # Required: nomes auto-gerados pelo CFN (sem fallback seguro porque
        # o nome legado "informs-tracking-*" não existe mais).
        location_table=_required("LOCATION_TABLE"),
        profile_table=_required("PROFILE_TABLE"),
        cognito_user_pool_id=_required("COGNITO_USER_POOL_ID"),
        cognito_app_client_id=_required("COGNITO_APP_CLIENT_ID"),
    )


def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Env var obrigatória ausente: {key}")
    return value
