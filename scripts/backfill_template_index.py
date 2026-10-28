"""Preenche o `TemplateIndex` (GSI4) nos formulários gravados antes dele.

Formulário criado depois do deploy do índice já nasce com GSI4PK/GSI4SK
(`FormRepositoryDynamo.create_form`). Os anteriores não aparecem no índice: o
template pareceria livre para edição, e eles não entrariam na lista de
propagação de versão. Este script varre a tabela e grava nesses itens:

- `GSI4PK = template#{template}` e `GSI4SK = created_at#{created_at:013d}#{form_id}`;
- `template_version = 1` quando ainda não houver (mesmo default do app).

Só mexe em item de formulário (`PK` começando com `form#`) cujo `template` é
um UUID e que ainda não tem `GSI4PK`. Idempotente: rodar de novo não muda o
que já foi preenchido.

Uso (depois do `cdk deploy` que cria o índice, uma vez por ambiente):

    # mostra o que mudaria, sem gravar
    AWS_REGION=sa-east-1 python scripts/backfill_template_index.py --table <nome-da-tabela>

    # grava
    AWS_REGION=sa-east-1 python scripts/backfill_template_index.py --table <nome-da-tabela> --apply

O nome físico da tabela de formulários está no console do DynamoDB (é o que a
Lambda recebe em `DYNAMO_TABLE_NAME`).
"""

import argparse
import os
import sys
from uuid import UUID

import boto3
from boto3.dynamodb.conditions import Attr

REGION = os.environ.get("AWS_REGION", "sa-east-1")


def _is_uuid(value) -> bool:
    try:
        UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False


def _needs_backfill(item: dict) -> bool:
    return (
        isinstance(item.get("PK"), str)
        and item["PK"].startswith("form#")
        and "GSI4PK" not in item
        and _is_uuid(item.get("template"))
        and item.get("created_at") is not None
    )


def _index_values(item: dict) -> dict:
    form_id = item["PK"].split("form#", 1)[1]
    values = {
        "GSI4PK": f"template#{item['template']}",
        "GSI4SK": f"created_at#{int(item['created_at']):013d}#{form_id}",
    }
    if item.get("template_version") is None:
        values["template_version"] = 1
    return values


def _scan_forms(table):
    kwargs = {
        "FilterExpression": Attr("PK").begins_with("form#") & Attr("template").exists(),
        "ProjectionExpression": "PK, SK, #tpl, created_at, template_version, GSI4PK",
        "ExpressionAttributeNames": {"#tpl": "template"},
    }
    while True:
        resp = table.scan(**kwargs)
        yield from resp.get("Items", [])
        if "LastEvaluatedKey" not in resp:
            return
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def run(table_name: str, apply: bool) -> int:
    table = boto3.resource("dynamodb", region_name=REGION).Table(table_name)
    scanned = pending = written = 0

    for item in _scan_forms(table):
        scanned += 1
        if not _needs_backfill(item):
            continue
        pending += 1
        values = _index_values(item)
        if not apply:
            continue
        names = {f"#a{i}": key for i, key in enumerate(values)}
        table.update_item(
            Key={"PK": item["PK"], "SK": item["SK"]},
            UpdateExpression="SET " + ", ".join(f"#a{i} = :v{i}" for i in range(len(values))),
            # Não sobrescreve o que um deploy novo já gravou nesse meio-tempo.
            ConditionExpression="attribute_not_exists(GSI4PK)",
            ExpressionAttributeNames=names,
            ExpressionAttributeValues={f":v{i}": value for i, value in enumerate(values.values())},
        )
        written += 1

    mode = "gravados" if apply else "a gravar (rode com --apply)"
    print(f"Formulários lidos: {scanned} · sem índice: {pending} · {mode}: {written if apply else pending}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--table", required=True, help="Nome físico da tabela de formulários")
    parser.add_argument("--apply", action="store_true", help="Grava (sem isto, só conta)")
    args = parser.parse_args()
    return run(args.table, args.apply)


if __name__ == "__main__":
    sys.exit(main())
