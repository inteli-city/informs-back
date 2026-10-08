"""Variáveis de ambiente do ambiente local (DynamoDB Local + LocalStack).

Importe este módulo ANTES de qualquer `src.*`: o `Environments` lê o ambiente
na primeira chamada e os presenters instanciam os repositórios no import.

Tudo aqui é `setdefault` — uma variável já definida no shell vence. Os nomes
apontam para `localhost` porque a API local roda no host, não num container:
assim o endereço que o boto3 usa para assinar URLs do S3 é o mesmo que o
navegador consegue abrir.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LOCAL_DEFAULTS = {
    "STAGE": "DEV",
    "REGION": "sa-east-1",
    "AWS_DEFAULT_REGION": "sa-east-1",
    # DynamoDB Local e LocalStack aceitam qualquer credencial, mas o boto3 exige
    # que exista uma — sem isto ele sai procurando no ~/.aws do usuário.
    "AWS_ACCESS_KEY_ID": "local",
    "AWS_SECRET_ACCESS_KEY": "local",
    "ENDPOINT_URL": "http://localhost:8000",
    "DYNAMO_TABLE_NAME": "Formularios_Table",
    "DYNAMO_PARTITION_KEY": "PK",
    "DYNAMO_SORT_KEY": "SK",
    "DYNAMO_PROFILE_TABLE_NAME": "Formularios_Profiles_Table",
    "DYNAMO_LOCATION_TABLE_NAME": "Formularios_Locations_Table",
    "S3_ENDPOINT_URL": "http://localhost:4566",
    "BUCKET_NAME": "formularios-local",
    "GITHUB_REF_NAME": "local",
}


def _utf8_console() -> None:
    # O console do Windows (cp1252) quebra ao imprimir acento ou símbolo.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def apply_local_env() -> None:
    for key, value in LOCAL_DEFAULTS.items():
        os.environ.setdefault(key, value)


_utf8_console()
apply_local_env()
