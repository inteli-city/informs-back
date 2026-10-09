"""Grava uma camada da configuração da aplicação (padrão ou de um sistema).

Enquanto o Admin não existe, é por aqui que a configuração muda. O arquivo
JSON traz só as chaves que a camada altera — o resto vem do padrão (ver
`src/shared/domain/entities/app_config.py`). O conteúdo passa pelo mesmo
esquema que a API usa, então um typo é recusado antes de chegar ao banco.

Uso (mesmas variáveis de ambiente das Lambdas):

    STAGE=DEV REGION=sa-east-1 DYNAMO_TABLE_NAME=... \\
    DYNAMO_PARTITION_KEY=PK DYNAMO_SORT_KEY=SK \\
    python scripts/put_app_config.py --system UBERLANDIA --file scripts/app_config/uberlandia.json --dry-run

    # padrão da aplicação
    python scripts/put_app_config.py --default --file scripts/app_config/default.json

A camada gravada SUBSTITUI a anterior (não mescla): o arquivo é a fonte da
verdade. A versão só sobe quando o conteúdo muda — rodar duas vezes o mesmo
arquivo não gera versão nova. Os demais campos da SystemConfig (escopo,
geofence, allow_unassigned_forms) são preservados.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.shared.domain.entities.default_app_config import DefaultAppConfig  # noqa: E402
from src.shared.domain.entities.system_config import SystemConfig  # noqa: E402
from src.shared.environments import Environments  # noqa: E402


def _put_default(repo, values: dict, dry_run: bool, author: str) -> None:
    current = repo.get_default_app_config()
    current_values = current.values if current else {}
    if current_values == values:
        print("Padrão da aplicação já está igual ao arquivo. Nada a gravar.")
        return

    version = (current.version if current else 0) + 1
    config = DefaultAppConfig(values=values, version=version, updated_at=int(time.time() * 1000), updated_by=author)
    print(f"Padrão da aplicação: versão {version - 1} -> {version}")
    print(json.dumps(values, indent=2, ensure_ascii=False))
    if not dry_run:
        repo.put_default_app_config(config)


def _put_system(repo, system: str, values: dict, dry_run: bool) -> None:
    current = repo.get_by_system(system)
    current_values = current.app_config if current else {}
    if current_values == values:
        print(f"Configuração de {system} já está igual ao arquivo. Nada a gravar.")
        return

    now = int(time.time() * 1000)
    version = (current.app_config_version if current else 0) + 1
    config = SystemConfig(
        system=system,
        created_at=current.created_at if current else now,
        updated_at=now,
        scope_keys=current.scope_keys if current else None,
        scope_partition_key=current.scope_partition_key if current else None,
        geofence_radius_m=current.geofence_radius_m if current else None,
        allow_unassigned_forms=current.allow_unassigned_forms if current else False,
        app_config=values,
        app_config_version=version,
    )
    print(f"{system}: versão da configuração {version - 1} -> {version}")
    print(json.dumps(values, indent=2, ensure_ascii=False))
    if not dry_run:
        repo.put(config)


# Só as camadas versionadas no repositório vão para o banco: a configuração de
# produção tem histórico e revisão, e um caminho arbitrário no --file não lê
# nada fora daqui.
APP_CONFIG_DIR = (Path(__file__).resolve().parent / "app_config").resolve()


def _layer_file(file_arg: str) -> Path:
    path = Path(file_arg).resolve()
    if path.suffix != ".json" or not path.is_relative_to(APP_CONFIG_DIR):
        raise SystemExit(f"--file precisa ser um .json dentro de {APP_CONFIG_DIR}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Grava uma camada da configuração da aplicação")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--system", help="Sistema cuja camada será gravada (ex.: UBERLANDIA)")
    target.add_argument("--default", action="store_true", help="Grava o padrão da aplicação")
    parser.add_argument("--file", required=True, help="JSON com as chaves da camada")
    parser.add_argument("--dry-run", action="store_true", help="Valida e mostra o que mudaria, sem gravar")
    args = parser.parse_args()

    values = json.loads(_layer_file(args.file).read_text(encoding="utf-8"))
    repo = Environments.get_system_config_repo()

    if args.default:
        _put_default(repo, values, args.dry_run, author=os.environ.get("USER") or os.environ.get("USERNAME"))
    else:
        _put_system(repo, args.system, values, args.dry_run)

    if args.dry_run:
        print("--dry-run: nada foi gravado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
