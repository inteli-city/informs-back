#!/usr/bin/env python3
"""
Cria localmente as tabelas DynamoDB que o CDK cria na AWS
(`iac/iac/dynamo_stack.py`): formulários (com os três GSIs), perfis e
localização. Mantenha os índices em sincronia com o stack — um GSI que falta
aqui só aparece como erro de query em runtime.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_env  # noqa: E402,F401  (precisa vir antes de qualquer src.*)

import boto3  # noqa: E402
from botocore.exceptions import ClientError  # noqa: E402

from src.shared.environments import Environments  # noqa: E402

envs = Environments.get_envs()

dynamo_config = {"endpoint_url": envs.endpoint_url, "region_name": envs.region}
dynamodb = boto3.resource("dynamodb", **dynamo_config)
client = boto3.client("dynamodb", **dynamo_config)


def _gsi(name: str, pk: str, sk: str) -> dict:
    return {
        "IndexName": name,
        "KeySchema": [{"AttributeName": pk, "KeyType": "HASH"}, {"AttributeName": sk, "KeyType": "RANGE"}],
        "Projection": {"ProjectionType": "ALL"},
    }


def _string_attrs(*names: str) -> list:
    return [{"AttributeName": name, "AttributeType": "S"} for name in names]


def _table_specs() -> list:
    pk, sk = envs.dynamo_partition_key, envs.dynamo_sort_key
    key_schema = [{"AttributeName": pk, "KeyType": "HASH"}, {"AttributeName": sk, "KeyType": "RANGE"}]
    return [
        {
            "TableName": envs.dynamo_table_name,
            "KeySchema": key_schema,
            "AttributeDefinitions": _string_attrs(pk, sk, "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK", "GSI3PK", "GSI3SK"),
            "GlobalSecondaryIndexes": [
                _gsi("UserPriorityIndex", "GSI1PK", "GSI1SK"),
                _gsi("SystemUpdatedAtIndex", "GSI2PK", "GSI2SK"),
                _gsi("PoolIndex", "GSI3PK", "GSI3SK"),
            ],
            "StreamSpecification": {"StreamEnabled": True, "StreamViewType": "NEW_IMAGE"},
        },
        {
            "TableName": envs.dynamo_profile_table_name,
            "KeySchema": [
                {"AttributeName": envs.dynamo_profile_partition_key, "KeyType": "HASH"},
                {"AttributeName": envs.dynamo_profile_sort_key, "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": _string_attrs(
                envs.dynamo_profile_partition_key, envs.dynamo_profile_sort_key, "GSI1PK", "GSI1SK"
            ),
            "GlobalSecondaryIndexes": [_gsi("ByRole", "GSI1PK", "GSI1SK")],
        },
        {
            "TableName": envs.dynamo_location_table_name,
            "KeySchema": [
                {"AttributeName": envs.dynamo_location_partition_key, "KeyType": "HASH"},
                {"AttributeName": envs.dynamo_location_sort_key, "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": _string_attrs(envs.dynamo_location_partition_key, envs.dynamo_location_sort_key),
        },
    ]


def delete_table(table_name: str) -> None:
    try:
        client.delete_table(TableName=table_name)
        client.get_waiter("table_not_exists").wait(TableName=table_name)
        print(f"[del]  Tabela '{table_name}' deletada")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise


def create_table(spec: dict) -> None:
    try:
        dynamodb.create_table(BillingMode="PAY_PER_REQUEST", **spec)
        client.get_waiter("table_exists").wait(TableName=spec["TableName"])
        print(f"[ok]   Tabela '{spec['TableName']}' criada")
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceInUseException":
            raise
        print(f"[skip] Tabela '{spec['TableName']}' já existe")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria as tabelas do DynamoDB local com os GSIs do CDK.")
    parser.add_argument("--reset", action="store_true", help="Deleta e recria as tabelas.")
    args = parser.parse_args()

    for spec in _table_specs():
        if args.reset:
            delete_table(spec["TableName"])
        create_table(spec)

    print(f"\n[ok] Tabelas: {client.list_tables()['TableNames']}")
    print("Veja os dados em http://localhost:8001")


if __name__ == "__main__":
    main()
