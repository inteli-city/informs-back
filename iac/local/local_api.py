#!/usr/bin/env python3
"""API local: o API Gateway das Lambdas, sem AWS e sem SAM.

Recebe HTTP, monta o mesmo evento que o API Gateway (REST, proxy) entregaria
e chama o `lambda_handler` do módulo **no mesmo processo**. Cada requisição
leva milissegundos — o `sam local start-api` sobe um container por chamada e
leva segundos, o que torna um teste ponta a ponta lento e instável.

Autenticação: como o autorizador local (`iac/authorizers/local_authorizer`),
lê as claims do JWT do header `Authorization` SEM validar assinatura. Serve
tanto o id_token de um login real no Gates quanto o token falso que o modo
de login local do front gera. Por isso ela só sobe em endereço de loopback
(`127.0.0.1`, `::1`, `localhost`): `--host 0.0.0.0` é recusado.

Uso (com DynamoDB Local e LocalStack de pé — ver `iac/LOCAL_SETUP.md`):

    python iac/local/local_api.py            # http://127.0.0.1:4010/mss-formularios
    python iac/local/local_api.py --port 4011

Porta 4010 e não 3000: a 3000 é a porta padrão de meio mundo de dev server, e
`localhost` pode resolver para IPv6 e cair em outro processo. Use sempre
`127.0.0.1` na URL.

As rotas espelham `iac/iac/lambda_stack.py`; o teste
`tests/iac/test_local_api_routes.py` falha se uma Lambda nova ficar de fora.
"""

import argparse
import base64
import importlib
import ipaddress
import json
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_env  # noqa: E402,F401  (precisa vir antes de qualquer src.*)

BASE_PATH = "/mss-formularios"


@dataclass(frozen=True)
class Route:
    method: str
    template: str
    module: str
    public: bool = False

    @property
    def segments(self) -> List[str]:
        return [seg for seg in self.template.split("/") if seg]


# Espelho de `lambda_stack.py`. Path params com os mesmos nomes do API Gateway
# ({form_id}, {template_id}, {user_id}) — é por eles que os controllers leem.
ROUTES: List[Route] = [
    Route("GET", "/permissions/actions", "get_permission_actions"),
    Route("GET", "/systems/{system}/roles", "get_system_roles"),
    Route("POST", "/systems/{system}/roles", "create_system_role"),
    Route("PUT", "/systems/{system}/roles/{role_id}", "update_system_role"),
    Route("DELETE", "/systems/{system}/roles/{role_id}", "delete_system_role"),
    Route("GET", "/systems/{system}/users", "get_system_users"),
    Route("PUT", "/systems/{system}/users/{user_id}", "put_system_user"),
    Route("DELETE", "/systems/{system}/users/{user_id}", "delete_system_user"),
    Route("POST", "/forms", "create_form"),
    Route("GET", "/forms", "get_all_forms"),
    Route("POST", "/forms/route-plan", "plan_route"),
    Route("POST", "/forms/sync-origin/callback", "sync_forms_origin_callback"),
    Route("GET", "/forms/{form_id}", "get_form"),
    Route("POST", "/forms/{form_id}/start", "start_form"),
    Route("POST", "/forms/{form_id}/submit", "submit_form"),
    Route("POST", "/forms/{form_id}/cancel", "cancel_form"),
    Route("POST", "/forms/{form_id}/claim", "claim_form"),
    Route("POST", "/forms/{form_id}/release", "release_form"),
    Route("POST", "/forms/{form_id}/assign", "assign_form"),
    Route("POST", "/forms/{form_id}/files/refresh-presign", "refresh_presign"),
    Route("POST", "/profiles", "create_profile"),
    Route("POST", "/profiles/login", "login_profile"),
    Route("DELETE", "/profiles/{user_id}", "delete_profile"),
    Route("PUT", "/profiles/{user_id}", "update_profile"),
    Route("GET", "/locations/history", "get_location_history"),
    Route("POST", "/templates", "create_template"),
    Route("GET", "/templates", "get_all_templates"),
    Route("PUT", "/templates/{template_id}", "update_template"),
    Route("GET", "/templates/{template_id}", "get_template"),
    Route("GET", "/app-config", "get_app_config"),
    Route("GET", "/app-config/admin", "get_app_config_admin"),
    Route("PUT", "/app-config/default", "put_default_app_config"),
    Route("PUT", "/app-config/systems/{system}", "put_system_app_config"),
    Route("GET", "/docs", "docs", public=True),
]


def _match_segments(segments, parts) -> Optional[Tuple[Dict[str, str], int]]:
    """Parâmetros capturados e quantos segmentos literais bateram; None se não casa."""
    params: Dict[str, str] = {}
    literal_hits = 0
    for expected, actual in zip(segments, parts):
        if expected.startswith("{") and expected.endswith("}"):
            params[expected[1:-1]] = actual
        elif expected == actual:
            literal_hits += 1
        else:
            return None
    return params, literal_hits


def match_route(method: str, path: str) -> Tuple[Optional[Route], Dict[str, str]]:
    """Segmento literal vence parâmetro: `/forms/route-plan` antes de `/forms/{form_id}`."""
    parts = [seg for seg in path.split("/") if seg]
    best: Tuple[Optional[Route], Dict[str, str], int] = (None, {}, -1)
    for route in ROUTES:
        if route.method != method or len(route.segments) != len(parts):
            continue
        matched = _match_segments(route.segments, parts)
        if matched is not None and matched[1] > best[2]:
            best = (route, matched[0], matched[1])
    return best[0], best[1]


def claims_from_authorization(header: Optional[str]) -> Optional[dict]:
    """Mesma normalização do autorizador local: só as claims que os presenters leem."""
    if not header:
        return None
    token = header.split(" ", 1)[1].strip() if header.lower().startswith("bearer ") else header.strip()
    parts = token.split(".")
    if len(parts) < 2:
        return None
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload.encode("utf-8")))
    except ValueError:  # inclui json.JSONDecodeError
        return None

    groups = claims.get("cognito:groups", [])
    return {
        "sub": claims.get("sub", ""),
        "name": claims.get("name") or claims.get("cognito:username") or "",
        "email": claims.get("email", ""),
        "cognito:groups": ",".join(groups) if isinstance(groups, list) else str(groups or ""),
    }


def build_event(method: str, route: Route, path: str, params: Dict[str, str], query: str,
                headers: Dict[str, str], body: Optional[str], claims: Optional[dict]) -> dict:
    multi = parse_qs(query, keep_blank_values=True)
    return {
        "resource": route.template,
        "path": path,
        "httpMethod": method,
        "headers": headers,
        "queryStringParameters": {key: values[-1] for key, values in multi.items()} or None,
        "multiValueQueryStringParameters": multi or None,
        "pathParameters": params or None,
        "body": body,
        "isBase64Encoded": False,
        "requestContext": {
            "resourcePath": route.template,
            "httpMethod": method,
            "path": BASE_PATH + path,
            "authorizer": {"claims": claims} if claims else {},
        },
    }


_presenters: Dict[str, object] = {}
# Os presenters guardam repositórios em variáveis de módulo; uma requisição por
# vez evita corrida nesse estado. Localmente, a vazão nunca é o gargalo.
_invoke_lock = threading.Lock()


# O primeiro import de cada presenter também é serializado: o navegador abre
# várias requisições de uma vez, e importar módulos com imports em ciclo em
# threads paralelas trava o Python (`_DeadlockError` no lock de import).
_import_lock = threading.Lock()


def load_presenter(module: str):
    with _import_lock:
        if module not in _presenters:
            _presenters[module] = importlib.import_module(f"src.modules.{module}.app.{module}_presenter")
        return _presenters[module]


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Max-Age": "600",
}
# Os únicos headers que o app manda para a API. Lista fixa: devolver o
# `Access-Control-Request-Headers` da requisição seria refletir entrada do
# cliente na resposta.
CORS_ALLOWED_HEADERS = "Authorization,Content-Type"


class LocalApiHandler(BaseHTTPRequestHandler):
    server_version = "InformsLocalAPI/1.0"

    def do_OPTIONS(self):
        self._send(204, {**CORS_HEADERS, "Access-Control-Allow-Headers": CORS_ALLOWED_HEADERS}, b"")

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def _dispatch(self, method: str) -> None:
        started = time.perf_counter()
        url = urlsplit(self.path)
        path = url.path[len(BASE_PATH):] if url.path.startswith(BASE_PATH) else url.path
        path = "/" + path.strip("/")

        route, params = match_route(method, path)
        if route is None:
            # O caminho pedido vai para o terminal, não para a resposta: ecoar
            # entrada da requisição no corpo é XSS refletido (Sonar S5131).
            print(f"{method:6} 404 rota inexistente na API local: {path}", flush=True)
            return self._json(404, {"message": "Rota não existe na API local"}, started)

        claims = claims_from_authorization(self.headers.get("Authorization"))
        if claims is None and not route.public:
            return self._json(401, {"message": "Unauthorized"}, started)

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8") if length else None
        event = build_event(method, route, path, params, url.query, dict(self.headers.items()), body, claims)

        try:
            presenter = load_presenter(route.module)
        except ModuleNotFoundError:
            return self._json(501, {"message": f"O módulo '{route.module}' não existe nesta branch"}, started)

        try:
            with _invoke_lock:
                result = presenter.lambda_handler(event, None)
        except Exception:
            traceback.print_exc()
            return self._json(500, {"message": f"Erro não tratado em {route.module} (veja o terminal da API local)"}, started)

        headers = {**CORS_HEADERS, **(result.get("headers") or {})}
        # A resposta da Lambda pode ecoar o que veio na requisição. Nunca servir
        # como HTML: sem Content-Type da Lambda vale JSON, e `nosniff` impede o
        # navegador de adivinhar outro tipo.
        if not any(key.lower() == "content-type" for key in headers):
            headers["Content-Type"] = "application/json"
        headers["X-Content-Type-Options"] = "nosniff"
        payload = result.get("body") or ""
        if result.get("isBase64Encoded"):
            raw = base64.b64decode(payload)
        else:
            raw = payload.encode("utf-8") if isinstance(payload, str) else json.dumps(payload).encode("utf-8")
        self._send(int(result.get("statusCode", 200)), headers, raw, started, route.module)

    def _json(self, status: int, body: dict, started: float) -> None:
        self._send(status, {**CORS_HEADERS, "Content-Type": "application/json"}, json.dumps(body).encode("utf-8"), started)

    def _send(self, status: int, headers: dict, raw: bytes, started: Optional[float] = None, module: str = "-") -> None:
        self.send_response(status)
        for key, value in headers.items():
            if key.lower() != "content-length":
                self.send_header(key, value)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if raw:
            self.wfile.write(raw)
        if started is not None:
            elapsed = (time.perf_counter() - started) * 1000
            print(f"{self.command:6} {status} {self.path} -> {module} ({elapsed:.0f} ms)", flush=True)

    def log_message(self, format, *args):  # noqa: A002 — assinatura da stdlib
        # A linha por requisição já sai em `_send`, com o módulo e o tempo.
        pass


def is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="API local do Informs (Lambdas em processo).")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4010)
    args = parser.parse_args()

    # A API aceita qualquer token: fora do loopback, qualquer um na rede
    # entraria como quem quisesse.
    if not is_loopback(args.host):
        raise SystemExit(f"--host {args.host!r} recusado: a API local só escuta em loopback (ex.: 127.0.0.1)")

    server = ThreadingHTTPServer((args.host, args.port), LocalApiHandler)
    print(f"API local ouvindo em {args.host}:{args.port}, base {BASE_PATH}  (Ctrl+C para parar)", flush=True)
    try:
        # HTTP sem TLS de propósito: servidor de desenvolvimento, só em loopback (checado acima).
        server.serve_forever()  # NOSONAR
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
