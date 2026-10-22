#!/usr/bin/env python3
"""E2E local da sincronização de Uberlândia com o Apex (parte 2 do plano informs-uberlandia-sync).

Roda os handlers reais de `sync_forms_origin` e `sync_forms_origin_callback` contra o DynamoDB Local
(preparado por `bootstrap_local.py --reset-db --seed`) e contra um Apex falso, em 127.0.0.1. Não abre
conexão para host que não seja local: uma guarda monta a URL de cada origem antes de qualquer cenário
e aborta com exit 2 se alguma sair de localhost. Não usa segredo nem AWS real.

Uso (com o DynamoDB Local e o LocalStack de pé):
    python iac/local/e2e_sync_uberlandia.py --saida DIR
    python iac/local/e2e_sync_uberlandia.py --so-guarda --sem-sobrescrita-de gaia   # prova que a guarda recusa

Cada cenário imprime PASS, FAIL ou NAO_MEDIDO com o que foi medido. Exit 0 só se todos passarem.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlsplit

# Antes de qualquer `src.*`: o `local_env` põe o endpoint local (DynamoDB e LocalStack) no ambiente.
import local_env  # noqa: F401
from saida_e2e import pasta_de_saida

import boto3
from boto3.dynamodb.conditions import Attr, Key

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
FORMS_TO_CREATE = 120
PREFIXO_FORM = "form#"
PATH_PREFIX = "/ords"


@dataclass
class Resultado:
    cenario: str
    status: str  # PASS, FAIL ou NAO_MEDIDO
    medido: str
    detalhe: dict[str, Any] = field(default_factory=dict)


RESULTADOS: list[Resultado] = []


def registrar(cenario: str, ok: bool | None, medido: str, detalhe: dict[str, Any] | None = None) -> None:
    if ok is None:
        status = "NAO_MEDIDO"
    else:
        status = "PASS" if ok else "FAIL"
    RESULTADOS.append(Resultado(cenario, status, medido, detalhe or {}))
    print(f"[{status}] {cenario}: {medido}", flush=True)


class FakeApex:
    """Apex falso: guarda cada requisição e responde o que o cenário pedir (ok ou 500)."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.mode = "ok"
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802 - nome imposto pelo http.server
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length).decode("utf-8")
                try:
                    body = json.loads(raw)
                except ValueError:
                    body = {"_invalido": raw[:200]}
                fake.requests.append({"path": self.path, "body": body})
                if fake.mode == "fail":
                    status, payload = 500, {"error": "falha forçada pelo cenário"}
                else:
                    status, payload = 200, {"failed_form_ids": []}
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, format: str, *args: object) -> None:  # noqa: A002
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def clear(self) -> None:
        self.requests.clear()

    def paths(self) -> list[str]:
        return [item["path"] for item in self.requests]

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()


class Ctx:
    function_name = "sync-forms-origin-e2e"
    memory_limit_in_mb = 512
    invoked_function_arn = "arn:aws:lambda:sa-east-1:000000000000:function:e2e"
    aws_request_id = "e2e-request"


def configurar_overrides(apex: FakeApex, sem: set[str]) -> None:
    """APEX_URL_<ORIGEM> aponta cada origem para o Apex falso, com o mesmo alias do ORDS."""
    aliases = {"gaia": "gaia", "uberlandia": "supervisao", "servicos_poa": "servicos_poa"}
    for origem, alias in aliases.items():
        chave = f"APEX_URL_{origem.upper()}"
        if origem in sem:
            os.environ.pop(chave, None)
        else:
            os.environ[chave] = f"{apex.base}{PATH_PREFIX}/{alias}/informs/cadastrar_formulario"


def guarda() -> bool:
    """Monta a URL de toda origem pelo `_build_url` e recusa qualquer host que não seja local."""
    from src.shared.infra.repositories.origin_repository_apex import OriginRepositoryApex
    from src.shared.known_systems import SYSTEM_TO_ORIGIN

    repo = OriginRepositoryApex()
    ok = True
    for origem in sorted(set(SYSTEM_TO_ORIGIN.values())):
        url = repo._build_url(origem)
        host = urlsplit(url).hostname or ""
        local = host in LOCAL_HOSTS
        ok = ok and local
        print(f"[guarda] {origem}: host={host} local={local}", flush=True)
    if not ok:
        print("[guarda] RECUSADO: origem fora de localhost; nenhum cenário roda.", flush=True)
    return ok


def tabela():
    envs = local_env_envs()
    recurso = boto3.resource("dynamodb", endpoint_url=envs.endpoint_url, region_name=envs.region)
    return recurso.Table(envs.dynamo_table_name)


def local_env_envs():
    from src.shared.environments import Environments

    return Environments.get_envs()


def zerar_estado(sistema: str) -> None:
    """Apaga o checkpoint e os erros pendentes do sistema, para o próximo cenário começar do zero."""
    table = tabela()
    table.delete_item(Key={"PK": f"sync_state#sync_forms_origin#{sistema}", "SK": "METADATA"})
    pk = f"sync_error_form#sync_forms_origin#{sistema}"
    for item in consulta_todos(table, Key("PK").eq(pk)):
        table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})


def consulta_todos(table, condicao) -> list[dict[str, Any]]:
    itens: list[dict[str, Any]] = []
    parametros: dict[str, Any] = {"KeyConditionExpression": condicao}
    while True:
        resposta = table.query(**parametros)
        itens.extend(resposta.get("Items", []))
        if "LastEvaluatedKey" not in resposta:
            return itens
        parametros["ExclusiveStartKey"] = resposta["LastEvaluatedKey"]


def formularios_scan(sistema: str) -> list[dict[str, Any]]:
    """Todos os formulários do sistema, lidos direto do DynamoDB (sem passar pelo caminho do sync)."""
    table = tabela()
    itens: list[dict[str, Any]] = []
    parametros: dict[str, Any] = {
        "FilterExpression": Attr("PK").begins_with(PREFIXO_FORM) & Attr("system").eq(sistema),
    }
    while True:
        resposta = table.scan(**parametros)
        itens.extend(resposta.get("Items", []))
        if "LastEvaluatedKey" not in resposta:
            return itens
        parametros["ExclusiveStartKey"] = resposta["LastEvaluatedKey"]


def erros_pendentes(sistema: str) -> list[str]:
    table = tabela()
    pk = f"sync_error_form#sync_forms_origin#{sistema}"
    return sorted(item["SK"].split(PREFIXO_FORM, 1)[1] for item in consulta_todos(table, Key("PK").eq(pk)))


def checkpoint(sistema: str) -> dict[str, Any] | None:
    resposta = tabela().get_item(Key={"PK": f"sync_state#sync_forms_origin#{sistema}", "SK": "METADATA"})
    return resposta.get("Item")


def preparar_dados() -> dict[str, Any]:
    """Acrescenta formulários de Uberlândia (prova o lote de 100) e confere as OS sem dono do pool."""
    import seed_local
    from src.shared.environments import Environments
    from src.shared.domain.enums.form_origin_enum import FormOrigin

    repo = Environments.get_form_repo()
    template = SimpleNamespace(id=seed_local._id("template:UBERLANDIA"), system="UBERLANDIA")
    agora = int(time.time() * 1000)
    criados = 0
    for i in range(FORMS_TO_CREATE):
        chave = f"e2e-ube-{i:03d}"
        formulario = seed_local._form(
            chave, template, owner=seed_local.BOTH_USER_ID,
            form_title=f"E2E Uberlândia {i:03d}", external_id=f"E2E-{i:03d}",
            origin=FormOrigin.AI, service_type="RECUPERACAO_ASFALTICA",
            city="Uberlândia", street=f"Rua de teste {i:03d}", latitude=-18.92, longitude=-48.27,
        )
        if repo.get_form_by_id(user_id=formulario.user_id or "", form_id=formulario.id) is None:
            repo.create_form(formulario)
            criados += 1
    formularios = formularios_scan("UBERLANDIA")
    sem_dono = [item["PK"].split(PREFIXO_FORM, 1)[1] for item in formularios if item.get("user_id") is None]
    return {"criados": criados, "total_uberlandia": len(formularios), "sem_dono": sorted(sem_dono), "agora": agora}


def rodar_sync(env_extra: dict[str, str | None]) -> dict[str, Any]:
    """Roda o handler real do sync com o ambiente do cenário. Recarrega o módulo para reler as variáveis."""
    from src.shared.environments import Environments

    for chave, valor in env_extra.items():
        if valor is None:
            os.environ.pop(chave, None)
        else:
            os.environ[chave] = valor
    Environments._reset_instance()
    modulo = importlib.import_module("src.modules.sync_forms_origin.app.sync_forms_origin_presenter")
    modulo = importlib.reload(modulo)
    resposta = modulo.lambda_handler({"source": "aws.events", "detail-type": "Scheduled Event", "detail": {}}, Ctx())
    return json.loads(resposta["body"])


def rodar_callback(corpo: Any) -> tuple[int, Any]:
    """Chama o handler real do callback com o evento que o API Gateway entregaria."""
    from src.shared.environments import Environments

    Environments._reset_instance()
    modulo = importlib.import_module("src.modules.sync_forms_origin_callback.app.sync_forms_origin_callback_presenter")
    modulo = importlib.reload(modulo)
    evento = {
        "version": "2.0",
        "rawPath": "/mss-formularios/sync-origin/callback",
        "headers": {"content-type": "application/json"},
        "requestContext": {"http": {"method": "POST", "path": "/mss-formularios/sync-origin/callback"}},
        "body": json.dumps(corpo),
        "isBase64Encoded": False,
    }
    resposta = modulo.lambda_handler(evento, Ctx())
    corpo_resposta = resposta["body"]
    if isinstance(corpo_resposta, str):
        corpo_resposta = json.loads(corpo_resposta)
    return resposta["statusCode"], corpo_resposta


def cenarios(apex: FakeApex, dados: dict[str, Any]) -> None:
    from src.shared.environments import Environments

    repo = Environments.get_form_repo()
    lista_uberlandia = {"APEX_SYNC_ENABLED_ORIGINS": "uberlandia", "APEX_SYNC_ENABLED": None}
    sem_dono = dados["sem_dono"]
    _cenarios_envio(apex, dados, lista_uberlandia)
    alterados = _cenarios_checkpoint_e_falha(apex, repo, sem_dono, lista_uberlandia)
    _cenarios_callback(apex, alterados, sem_dono)
    _cenario_gaia_em_dev(apex, repo, lista_uberlandia)


def _cenarios_envio(apex: FakeApex, dados: dict[str, Any], lista_uberlandia: dict[str, Any]) -> None:
    sem_envio = {"APEX_SYNC_ENABLED_ORIGINS": None, "APEX_SYNC_ENABLED": None}
    total = dados["total_uberlandia"]
    sem_dono = dados["sem_dono"]

    # 1. Dev trava por padrão: nenhuma requisição, e o checkpoint avança.
    zerar_estado("UBERLANDIA")
    zerar_estado("GAIA")
    apex.clear()
    corpo = rodar_sync(sem_envio)
    ponto = checkpoint("UBERLANDIA")
    registrar(
        "1. DEV trava por padrão",
        len(apex.requests) == 0 and ponto is not None and int(ponto.get("checkpoint_synced_at", 0)) > 0,
        f"requisições ao Apex={len(apex.requests)}; checkpoint UBERLANDIA="
        f"{ponto.get('checkpoint_synced_at') if ponto else None}; sent={corpo['totals']['sent']}",
        {"requisicoes": len(apex.requests)},
    )

    # 2. Uberlândia habilitada, Gaia não: só o caminho do alias supervisao.
    zerar_estado("UBERLANDIA")
    zerar_estado("GAIA")
    apex.clear()
    rodar_sync(lista_uberlandia)
    caminhos = apex.paths()
    so_supervisao = bool(caminhos) and all(p == f"{PATH_PREFIX}/supervisao/informs/cadastrar_formulario" for p in caminhos)
    corpos_ok = all(set(item["body"].keys()) == {"forms", "execution_id"} for item in apex.requests)
    registrar(
        "2. Uberlândia habilitada, Gaia não",
        so_supervisao and corpos_ok,
        f"requisições={len(caminhos)}; caminhos={sorted(set(caminhos))}; corpos com forms+execution_id={corpos_ok}",
        {"caminhos": sorted(set(caminhos))},
    )
    apenas_gaia = [p for p in caminhos if "/gaia/" in p or "/servicos_poa/" in p]
    registrar(
        "2b. Gaia e GIPAV sem requisição com a lista de Uberlândia",
        len(apenas_gaia) == 0,
        f"requisições para gaia/servicos_poa={len(apenas_gaia)}",
    )

    # 3. Lotes: o primeiro tem 100; a soma bate com a contagem direta no DynamoDB.
    tamanhos = [len(item["body"].get("forms", [])) for item in apex.requests]
    enviados = sum(tamanhos)
    registrar(
        "3. Lotes de 100 e soma igual à contagem",
        bool(tamanhos) and tamanhos[0] == 100 and enviados == total and total > 100,
        f"lotes={tamanhos}; soma enviada={enviados}; formulários UBERLANDIA no DynamoDB={total}",
        {"lotes": tamanhos, "soma": enviados, "contagem": total},
    )

    # 4. Conteúdo: todo formulário tem system UBERLANDIA; as OS sem dono estão no envio.
    ids_enviados = {form["id"] for item in apex.requests for form in item["body"].get("forms", [])}
    todos_ube = all(form.get("system") == "UBERLANDIA" for item in apex.requests for form in item["body"].get("forms", []))
    sem_dono_enviadas = all(i in ids_enviados for i in sem_dono)
    registrar(
        "4. Conteúdo: system UBERLANDIA e OS sem dono enviadas",
        todos_ube and sem_dono_enviadas and len(sem_dono) >= 2,
        f"todos system=UBERLANDIA={todos_ube}; OS sem dono no DynamoDB={len(sem_dono)}; "
        f"enviadas={sem_dono_enviadas}",
        {"os_sem_dono": len(sem_dono)},
    )


def _cenarios_checkpoint_e_falha(
    apex: FakeApex, repo: Any, sem_dono: list[str], lista_uberlandia: dict[str, Any]
) -> list[str]:
    # 5. Checkpoint: rodada sem alteração envia 0; alterar um formulário envia só esse.
    apex.clear()
    rodar_sync(lista_uberlandia)
    sem_mudanca = len(apex.requests) == 0
    alvo = next(f for f in formularios_scan("UBERLANDIA") if f["PK"].split(PREFIXO_FORM, 1)[1] not in sem_dono)
    id_alvo = alvo["PK"].split(PREFIXO_FORM, 1)[1]
    repo.update_form(user_id=alvo.get("user_id") or "", form_id=id_alvo, updated_at=int(time.time() * 1000))
    apex.clear()
    rodar_sync(lista_uberlandia)
    so_alterado = [i for item in apex.requests for i in [f["id"] for f in item["body"].get("forms", [])]]
    registrar(
        "5. Checkpoint: sem mudança envia 0; uma alteração envia só ela",
        sem_mudanca and so_alterado == [id_alvo],
        f"sem mudança={len(apex.requests) if sem_mudanca else 'enviou'}; "
        f"após alterar um: enviados={so_alterado}",
    )

    # 6. Falha do Apex: erro registrado; checkpoint; reenvio na rodada seguinte.
    # Sem zerar o checkpoint: a janela do sync é só a dos formulários alterados logo abaixo.
    apex.clear()
    apex.mode = "fail"
    alterados = [f["PK"].split(PREFIXO_FORM, 1)[1] for f in formularios_scan("UBERLANDIA")[:3]]
    for i in alterados:
        repo.update_form(user_id="", form_id=i, updated_at=int(time.time() * 1000))
    corpo_falha = rodar_sync(lista_uberlandia)
    pendentes = erros_pendentes("UBERLANDIA")
    ponto_falha = checkpoint("UBERLANDIA")
    ids_falha = sorted({f["id"] for item in apex.requests for f in item["body"].get("forms", [])})
    registrar(
        "6a. Falha do Apex grava SyncErrorForm para os formulários do lote",
        set(pendentes) == set(alterados) and corpo_falha["totals"]["failed"] == len(alterados),
        f"enviados na falha={ids_falha}; erros pendentes={len(pendentes)} de {len(alterados)}; "
        f"failed={corpo_falha['totals']['failed']}; checkpoint após falha="
        f"{ponto_falha.get('checkpoint_synced_at') if ponto_falha else None}",
        {"checkpoint_apos_falha": ponto_falha.get("checkpoint_synced_at") if ponto_falha else None},
    )
    apex.mode = "ok"
    apex.clear()
    rodar_sync(lista_uberlandia)
    reenviados = sorted({f["id"] for item in apex.requests for f in item["body"].get("forms", [])})
    registrar(
        "6b. Apex saudável reenvia os erros pendentes e limpa a fila de erro",
        set(alterados).issubset(set(reenviados)) and erros_pendentes("UBERLANDIA") == [],
        f"reenviados={len(reenviados)}; os 3 com erro reenviados={set(alterados).issubset(set(reenviados))}; "
        f"erros pendentes depois={len(erros_pendentes('UBERLANDIA'))}",
    )
    return alterados


def _cenarios_callback(apex: FakeApex, alterados: list[str], sem_dono: list[str]) -> None:
    # 7. Callback: ids válidos, id inexistente, corpo inválido e OS sem dono.
    valido = alterados[0]
    status_ok, corpo_ok = rodar_callback({"form_ids": [valido, sem_dono[0]], "execution_id": "exec-e2e"})
    salvos = corpo_ok.get("saved_error_forms", []) if isinstance(corpo_ok, dict) else []
    registrar(
        "7a. Callback com ids válidos registra no system do formulário (inclui OS sem dono)",
        status_ok == 200 and {s["form_id"] for s in salvos} == {valido, sem_dono[0]}
        and all(s["system"] == "UBERLANDIA" for s in salvos),
        f"status={status_ok}; registrados={sorted(s['form_id'] for s in salvos)}; system={sorted({s['system'] for s in salvos})}",
    )
    status_404, _ = rodar_callback({"form_ids": ["id-que-nao-existe"], "execution_id": "exec-e2e"})
    registrar("7b. Callback com id inexistente responde 404", status_404 == 404, f"status={status_404}")
    status_400, _ = rodar_callback({"form_ids": [], "execution_id": "exec-e2e"})
    registrar("7c. Callback com corpo inválido responde 400", status_400 == 400, f"status={status_400}")
    registrar(
        "7d. OS sem dono: erro registrado sem falha por falta de user_id",
        status_ok == 200 and sem_dono[0] in {s["form_id"] for s in salvos},
        "coberto em 7a: a OS sem dono foi registrada com status 200",
    )


def _cenario_gaia_em_dev(apex: FakeApex, repo: Any, lista_uberlandia: dict[str, Any]) -> None:
    # 8. Regressão: Gaia alterada, em DEV com a lista de Uberlândia, não envia.
    zerar_estado("GAIA")
    gaia = formularios_scan("GAIA")
    for item in gaia[:3]:
        repo.update_form(user_id=item.get("user_id") or "", form_id=item["PK"].split(PREFIXO_FORM, 1)[1],
                         updated_at=int(time.time() * 1000))
    apex.clear()
    rodar_sync(lista_uberlandia)
    gaia_req = [p for p in apex.paths() if "/gaia/" in p]
    registrar(
        "8. Gaia alterada em DEV com a lista de Uberlândia: 0 requisições de Gaia",
        len(gaia_req) == 0,
        f"formulários GAIA alterados={min(3, len(gaia))}; requisições para gaia={len(gaia_req)}",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="E2E local da sincronização de Uberlândia com o Apex (Apex falso em 127.0.0.1).",
    )
    parser.add_argument(
        "--saida", default=None,
        help="subpasta de iac/local/.e2e-saida onde gravar resultado.json (caminho fora dela é recusado)",
    )
    parser.add_argument("--so-guarda", action="store_true", help="roda só a guarda de host local e sai")
    parser.add_argument(
        "--sem-sobrescrita-de",
        action="append",
        default=[],
        choices=["gaia", "uberlandia", "servicos_poa"],
        help="não define APEX_URL_<ORIGEM> para a origem (usada para provar que a guarda recusa)",
    )
    args = parser.parse_args()
    # Valida o --saida antes de qualquer cenário: um caminho fora da pasta fixa para sem rodar nada.
    saida = pasta_de_saida(args.saida) if args.saida else None

    inicio = time.time()
    apex = FakeApex()
    sem = set(args.sem_sobrescrita_de)
    try:
        configurar_overrides(apex, sem)
        os.environ.setdefault("SYNC_FORMS_FIRST_RUN_FULL_SYNC", "true")
        os.environ.setdefault("SYNC_FORMS_TIMEOUT", "5")

        if not guarda():
            return 2
        if args.so_guarda:
            return 0

        dados = preparar_dados()
        print(f"[dados] criados={dados['criados']} total_UBERLANDIA={dados['total_uberlandia']} "
              f"sem_dono={len(dados['sem_dono'])}", flush=True)
        if dados["total_uberlandia"] <= 100:
            registrar("0. Dados de teste", False, f"{dados['total_uberlandia']} formulários, precisa de mais de 100")
            return 1
        cenarios(apex, dados)
    finally:
        apex.stop()

    total = len(RESULTADOS)
    passaram = sum(1 for r in RESULTADOS if r.status == "PASS")
    duracao = round(time.time() - inicio, 1)
    print(f"\nRESUMO: {passaram}/{total} PASS em {duracao}s", flush=True)
    if saida:
        saida.mkdir(parents=True, exist_ok=True)
        (saida / "resultado.json").write_text(
            json.dumps({"duracao_s": duracao, "cenarios": [r.__dict__ for r in RESULTADOS]},
                       ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    return 0 if passaram == total and total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
