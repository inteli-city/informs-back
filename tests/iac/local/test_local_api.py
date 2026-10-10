import base64
import json
import os
import re
import sys
from pathlib import Path

import pytest

# Antes de importar a API local: ela aplica os defaults do ambiente local com
# setdefault, e a suíte precisa continuar nos repositórios mock.
os.environ["STAGE"] = "TEST"

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "iac" / "local"))
sys.path.insert(0, str(REPO_ROOT))

import local_api  # noqa: E402


def _token(claims: dict) -> str:
    def b64(data: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    return f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64(claims)}.local"


# Lambdas disparadas pelo EventBridge Scheduler, sem rota no API Gateway.
SCHEDULED_ONLY = {"sync_forms_origin", "reconcile_form_files"}


def _http_modules_in_cdk() -> set:
    source = (REPO_ROOT / "iac" / "iac" / "lambda_stack.py").read_text(encoding="utf-8")
    modules = set(re.findall(r'module_name="([a-z_]+)"', source))
    modules.update(re.findall(r'_module_name = "([a-z_]+)"', source))
    return modules - SCHEDULED_ONLY


class TestRoutes:
    def test_every_http_lambda_in_cdk_has_a_local_route(self):
        local_modules = {route.module for route in local_api.ROUTES}
        missing = _http_modules_in_cdk() - local_modules
        assert not missing, f"Lambdas sem rota na API local: {sorted(missing)}"

    def test_literal_segment_wins_over_path_param(self):
        route, params = local_api.match_route("POST", "/forms/route-plan")
        assert route.module == "plan_route"
        assert params == {}

    def test_path_params_use_api_gateway_names(self):
        route, params = local_api.match_route("POST", "/forms/abc-123/files/refresh-presign")
        assert route.module == "refresh_presign"
        assert params == {"form_id": "abc-123"}

    def test_method_is_part_of_the_match(self):
        route, _ = local_api.match_route("PUT", "/templates/t-1")
        assert route.module == "update_template"
        route, _ = local_api.match_route("PATCH", "/templates/t-1")
        assert route is None


class TestClaims:
    def test_reads_claims_without_validating_signature(self):
        token = _token({"sub": "u-1", "email": "a@b.c", "name": "Ana", "cognito:groups": ["FORMULARIOS", "GAIA"]})
        claims = local_api.claims_from_authorization(f"Bearer {token}")
        assert claims == {"sub": "u-1", "name": "Ana", "email": "a@b.c", "cognito:groups": "FORMULARIOS,GAIA"}

    def test_missing_or_malformed_token(self):
        assert local_api.claims_from_authorization(None) is None
        assert local_api.claims_from_authorization("Bearer nope") is None


class TestEventToPresenter:
    def test_event_reaches_presenter_like_api_gateway(self):
        route, params = local_api.match_route("GET", "/templates")
        claims = {"sub": "user-123", "name": "User", "email": "user@test.com", "cognito:groups": "FORMULARIOS,GAIA"}
        event = local_api.build_event("GET", route, "/templates", params, "limit=5", {}, None, claims)

        result = local_api.load_presenter(route.module).lambda_handler(event, None)

        assert result["statusCode"] == 200
        assert "templates" in json.loads(result["body"])
        assert event["queryStringParameters"] == {"limit": "5"}


class TestLoopbackOnly:
    """A API local aceita qualquer token: só pode escutar em loopback."""

    def test_loopback_hosts_are_accepted(self):
        for host in ("127.0.0.1", "127.0.0.2", "::1", "localhost"):
            assert local_api.is_loopback(host), host

    def test_other_hosts_are_refused(self):
        for host in ("0.0.0.0", "::", "192.168.0.10", "meu-pc.local"):
            assert not local_api.is_loopback(host), host

    def test_main_refuses_non_loopback_host(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["local_api.py", "--host", "0.0.0.0"])
        with pytest.raises(SystemExit, match="recusado"):
            local_api.main()
