"""Migração da tabela Profiles do nome legado pro nome novo (auto-gerado).

Contexto: PR #49 removeu `table_name="informs-tracking-profile-{stage}"` do
CDK pra deixar o CFN gerar o nome físico seguindo o padrão da stack
(`FormulariosStack{stage}-FormulariosDynamoProfilesTable...-...`). Isso é
uma mudança DESTRUTIVA — o CFN vai DELETE+CREATE a tabela. Os dados
precisam ser migrados manualmente.

Sequência de uso:

    # 1. ANTES do `cdk deploy`: salvar dump do estado atual
    AWS_REGION=sa-east-1 python scripts/migrate_profile_table.py --stage dev dump

    # 2. cdk deploy → CFN deleta a tabela velha e cria a nova com nome auto

    # 3. APÓS o deploy: descobrir o nome novo + restaurar
    AWS_REGION=sa-east-1 python scripts/migrate_profile_table.py --stage dev restore

Dump fica em ~/.cache/informs/profile-dump-{stage}.json (ou no diretório
indicado por --dump-dir). Idempotente: re-executar restore não duplica
itens (PutItem sobrescreve por PK/SK).

Sem deps externas além do boto3 (já presente no requirements do projeto).
"""

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import boto3


# Region puxa de env (cai pra default só quando rodando sem AWS_REGION).
# Resolve python:S6262 — Sonar não gosta de region hardcoded.
REGION = os.environ.get("AWS_REGION", "sa-east-1")
LEGACY_TABLE_TEMPLATE = "informs-tracking-profile-{stage}"

# Default em ~/.cache/informs (modo 700 do user) em vez de /tmp (world-writable).
# Resolve python:S5443. Override via flag --dump-dir.
_DEFAULT_DUMP_DIR = Path.home() / ".cache" / "informs"


class _DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def _dump_path(dump_dir: Path, stage: str) -> Path:
    return dump_dir / f"profile-dump-{stage}.json"


def _resolve_new_table_name(stage: str) -> str:
    """Lê o Output ProfileTableName da stack FormulariosStack{stage}."""
    cfn = boto3.client("cloudformation", region_name=REGION)
    stack_name = f"FormulariosStack{stage}"
    resp = cfn.describe_stacks(StackName=stack_name)
    outputs = resp["Stacks"][0].get("Outputs", [])
    for out in outputs:
        if out["OutputKey"] == "ProfileTableName":
            return out["OutputValue"]
    raise RuntimeError(
        f"Output 'ProfileTableName' não encontrado em {stack_name}. "
        "Garante que o cdk deploy do PR #49 já rodou."
    )


def cmd_dump(stage: str, dump_dir: Path) -> None:
    """Scan completo da tabela legada → JSON local."""
    table_name = LEGACY_TABLE_TEMPLATE.format(stage=stage)
    dump_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    dump_path = _dump_path(dump_dir, stage)
    print(f"==> Dump de {table_name} → {dump_path}")

    table = boto3.resource("dynamodb", region_name=REGION).Table(table_name)
    items: list[dict] = []
    kwargs: dict = {}
    while True:
        resp = table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    dump_path.write_text(json.dumps(items, cls=_DecimalEncoder, indent=2))
    dump_path.chmod(0o600)
    print(f"    {len(items)} itens salvos em {dump_path}")


def cmd_restore(stage: str, dump_dir: Path) -> None:
    """Lê o dump → put_item na tabela nova (descoberta via CFN Output)."""
    dump_path = _dump_path(dump_dir, stage)
    if not dump_path.exists():
        sys.exit(f"!! Dump não encontrado em {dump_path}. Roda `dump` primeiro.")

    new_table_name = _resolve_new_table_name(stage)
    print(f"==> Restore {dump_path} → {new_table_name}")

    items = json.loads(dump_path.read_text())
    if not items:
        print("    Nada a restaurar.")
        return

    # PutItem é idempotente nas mesmas chaves (sobrescreve). Usar batch_writer
    # economiza ~25× em throughput de write.
    table = boto3.resource("dynamodb", region_name=REGION).Table(new_table_name)
    with table.batch_writer() as batch:
        for raw in items:
            # Reconverte strings que eram Decimal pra Decimal (PutItem aceita
            # str/int/float/Decimal — mas Number attribute exige Decimal).
            cleaned = {
                k: (Decimal(v) if _looks_like_number(v) else v)
                for k, v in raw.items()
            }
            batch.put_item(Item=cleaned)

    print(f"    {len(items)} itens restaurados.")


def _looks_like_number(v) -> bool:
    """Detecta se um valor JSON deveria virar Decimal (era Number no DDB)."""
    if not isinstance(v, str):
        return False
    try:
        Decimal(v)
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=["dev", "homolog", "prod"])
    parser.add_argument(
        "--dump-dir",
        default=str(_DEFAULT_DUMP_DIR),
        help=f"Diretório do dump (default: {_DEFAULT_DUMP_DIR}). Modo 700.",
    )
    parser.add_argument("action", choices=["dump", "restore"])
    args = parser.parse_args()

    dump_dir = Path(args.dump_dir).expanduser()
    if args.action == "dump":
        cmd_dump(args.stage, dump_dir)
    else:
        cmd_restore(args.stage, dump_dir)


if __name__ == "__main__":
    main()
