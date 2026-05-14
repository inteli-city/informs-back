"""Migração da tabela Profiles do nome legado pro nome novo (auto-gerado).

Contexto: PR #49 removeu `table_name="informs-tracking-profile-{stage}"` do
CDK pra deixar o CFN gerar o nome físico seguindo o padrão da stack
(`FormulariosStack{stage}-FormulariosDynamoProfilesTable...-...`). Isso é
uma mudança DESTRUTIVA — o CFN vai DELETE+CREATE a tabela. Os dados
precisam ser migrados manualmente.

Sequência de uso:

    # 1. ANTES do `cdk deploy`: salvar dump do estado atual
    python scripts/migrate_profile_table.py --stage dev dump

    # 2. cdk deploy → CFN deleta a tabela velha e cria a nova com nome auto

    # 3. APÓS o deploy: descobrir o nome novo + restaurar
    python scripts/migrate_profile_table.py --stage dev restore

O dump fica em /tmp/profile-dump-{stage}.json. Idempotente: re-executar
restore não duplica itens (usa PutItem com mesma PK/SK).

Sem deps externas além do boto3 (já presente no requirements do projeto).
"""

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer


REGION = "sa-east-1"
LEGACY_TABLE_TEMPLATE = "informs-tracking-profile-{stage}"
DUMP_PATH_TEMPLATE = "/tmp/profile-dump-{stage}.json"


class _DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


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


def cmd_dump(stage: str) -> None:
    """Scan completo da tabela legada → JSON local."""
    table_name = LEGACY_TABLE_TEMPLATE.format(stage=stage)
    dump_path = Path(DUMP_PATH_TEMPLATE.format(stage=stage))
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
    print(f"    {len(items)} itens salvos em {dump_path}")


def cmd_restore(stage: str) -> None:
    """Lê o dump → put_item na tabela nova (descoberta via CFN Output)."""
    dump_path = Path(DUMP_PATH_TEMPLATE.format(stage=stage))
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
    parser.add_argument("action", choices=["dump", "restore"])
    args = parser.parse_args()

    if args.action == "dump":
        cmd_dump(args.stage)
    else:
        cmd_restore(args.stage)


if __name__ == "__main__":
    main()
