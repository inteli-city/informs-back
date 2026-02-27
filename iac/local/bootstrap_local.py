#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


LOCAL_DIR = Path(__file__).resolve().parent
IAC_DIR = LOCAL_DIR.parent


def _run(command: list[str], cwd: Path | None = None) -> None:
    where = str(cwd or Path.cwd())
    print(f"[run] ({where}) {' '.join(command)}")
    subprocess.run(command, check=True, cwd=str(cwd) if cwd else None)


def _resolve_compose_command() -> list[str]:
    candidates = (["docker", "compose"], ["docker-compose"])
    for candidate in candidates:
        try:
            subprocess.run(candidate + ["version"], check=True, capture_output=True, text=True)
            return candidate
        except Exception:
            continue
    raise RuntimeError(
        "Docker Compose não encontrado. Instale Docker Desktop (ou plugin docker compose) para continuar."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sobe dependências locais (Dynamo/LocalStack) e prepara tabela/GSIs."
    )
    parser.add_argument("--skip-compose", action="store_true", help="Não sobe docker compose.")
    parser.add_argument("--reset-db", action="store_true", help="Deleta e recria a tabela local.")
    args = parser.parse_args()

    try:
        if not args.skip_compose:
            compose = _resolve_compose_command()
            _run(compose + ["-f", "docker-compose.yml", "up", "-d"], cwd=LOCAL_DIR)

        create_db_command = [sys.executable, str(LOCAL_DIR / "create_dynamodb_tables.py")]
        if args.reset_db:
            create_db_command.append("--reset")
        _run(create_db_command, cwd=IAC_DIR)
    except subprocess.CalledProcessError as err:
        print(f"[error] comando falhou com exit code {err.returncode}")
        return err.returncode
    except RuntimeError as err:
        print(f"[error] {err}")
        return 1

    print("\n[ok] Ambiente local pronto.")
    print("[next] Rode: make local-api")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
