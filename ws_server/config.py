"""Config lido das env vars (setadas pelo systemd EnvironmentFile)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    stage: str  # "dev" | "homolog" | "prod"
    aws_region: str
    location_table: str  # informs-tracking-location-{stage}
    profile_table: str  # informs-tracking-profile-{stage}
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
    stage = _required("STAGE")
    return Settings(
        stage=stage,
        aws_region=_required("AWS_REGION"),
        location_table=os.environ.get(
            "LOCATION_TABLE", f"informs-tracking-location-{stage}"
        ),
        profile_table=os.environ.get(
            "PROFILE_TABLE", f"informs-tracking-profile-{stage}"
        ),
        cognito_user_pool_id=_required("COGNITO_USER_POOL_ID"),
        cognito_app_client_id=_required("COGNITO_APP_CLIENT_ID"),
    )


def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Env var obrigatória ausente: {key}")
    return value
