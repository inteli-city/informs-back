#!/usr/bin/env python3
"""Sobe e prepara o ambiente local: DynamoDB Local, LocalStack (S3), tabelas e bucket.

    python iac/local/bootstrap_local.py              # sobe e cria o que faltar
    python iac/local/bootstrap_local.py --reset-db   # recria as tabelas (apaga os dados)
    python iac/local/bootstrap_local.py --seed       # e popula com dados de exemplo

Depois: `python iac/local/local_api.py`. Guia completo em `iac/LOCAL_SETUP.md`.
"""
import argparse
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

LOCAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(LOCAL_DIR))
import local_env  # noqa: E402,F401  (precisa vir antes de qualquer src.*)

import boto3  # noqa: E402

from src.shared.environments import Environments  # noqa: E402

WAIT_TIMEOUT_S = 60


def _run(command: list, cwd: Path = None) -> None:
    print(f"[run] {' '.join(command)}")
    subprocess.run(command, check=True, cwd=str(cwd) if cwd else None)


def _compose_command() -> list:
    for candidate in (["docker", "compose"], ["docker-compose"]):
        try:
            subprocess.run(candidate + ["version"], check=True, capture_output=True, text=True)
            return candidate
        except Exception:
            continue
    raise RuntimeError("Docker Compose não encontrado. Instale o Docker Desktop (ou o plugin docker compose).")


def _wait(description: str, probe) -> None:
    deadline = time.time() + WAIT_TIMEOUT_S
    while True:
        try:
            probe()
            print(f"[ok] {description} pronto")
            return
        except Exception as err:
            if time.time() > deadline:
                raise RuntimeError(f"{description} não respondeu em {WAIT_TIMEOUT_S}s: {err}")
            time.sleep(1)


def _ensure_bucket() -> None:
    envs = Environments.get_envs()
    s3 = boto3.client("s3", endpoint_url=envs.s3_endpoint_url, region_name=envs.region)
    existing = {bucket["Name"] for bucket in s3.list_buckets().get("Buckets", [])}
    if envs.bucket_name not in existing:
        s3.create_bucket(
            Bucket=envs.bucket_name,
            CreateBucketConfiguration={"LocationConstraint": envs.region},
        )
        print(f"[ok] bucket '{envs.bucket_name}' criado")
    # O app sobe as fotos direto do navegador (PUT na URL assinada) e as lê de
    # volta pela URL do objeto: sem CORS o navegador bloqueia as duas coisas.
    s3.put_bucket_cors(
        Bucket=envs.bucket_name,
        ExpectedBucketOwner=local_env.LOCALSTACK_ACCOUNT_ID,
        CORSConfiguration={
            "CORSRules": [{
                "AllowedOrigins": ["*"],
                "AllowedMethods": ["GET", "PUT", "HEAD"],
                "AllowedHeaders": ["*"],
                "ExposeHeaders": ["ETag"],
            }]
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepara o ambiente local do Informs.")
    parser.add_argument("--skip-compose", action="store_true", help="Não sobe o docker compose.")
    parser.add_argument("--reset-db", action="store_true", help="Apaga e recria as tabelas.")
    parser.add_argument("--seed", action="store_true", help="Popula com dados de exemplo (seed_local.py).")
    args = parser.parse_args()

    envs = Environments.get_envs()
    try:
        if not args.skip_compose:
            _run(_compose_command() + ["-f", "docker-compose.yml", "up", "-d"], cwd=LOCAL_DIR)

        dynamo = boto3.client("dynamodb", endpoint_url=envs.endpoint_url, region_name=envs.region)
        _wait("DynamoDB Local", dynamo.list_tables)
        _wait("LocalStack", lambda: urllib.request.urlopen(f"{envs.s3_endpoint_url}/_localstack/health", timeout=2))

        tables_command = [sys.executable, str(LOCAL_DIR / "create_dynamodb_tables.py")]
        if args.reset_db:
            tables_command.append("--reset")
        _run(tables_command)
        _ensure_bucket()

        if args.seed:
            _run([sys.executable, str(LOCAL_DIR / "seed_local.py")])
    except subprocess.CalledProcessError as err:
        print(f"[error] comando falhou com exit code {err.returncode}")
        return err.returncode
    except RuntimeError as err:
        print(f"[error] {err}")
        return 1

    print("\n[ok] Ambiente local pronto.")
    print("[next] python iac/local/local_api.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
