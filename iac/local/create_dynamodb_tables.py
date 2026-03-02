#!/usr/bin/env python3
"""
Script para criar as tabelas DynamoDB localmente baseado na estrutura do CDK
"""
import argparse
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Allow direct execution without requiring PYTHONPATH=.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.shared.environments import Environments

envs = Environments.get_envs()
table_name = envs.dynamo_table_name

dynamo_config = {
    "endpoint_url": envs.endpoint_url,
    "region_name": envs.region,
}

# Local DynamoDB requires credentials even if they are dummy values.
if envs.endpoint_url and "localhost" in envs.endpoint_url:
    dynamo_config["aws_access_key_id"] = "local"
    dynamo_config["aws_secret_access_key"] = "local"

dynamodb = boto3.resource("dynamodb", **dynamo_config)
client = boto3.client("dynamodb", **dynamo_config)

def delete_table(table_name):
    """Deleta uma tabela do DynamoDB Local"""
    try:
        client.delete_table(TableName=table_name)
        print(f"🗑️  Tabela '{table_name}' deletada com sucesso!")
        
        # Aguarda a tabela ser deletada
        waiter = client.get_waiter('table_not_exists')
        waiter.wait(TableName=table_name)
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"ℹ️  Tabela '{table_name}' não existe")
        else:
            print(f"❌ Erro ao deletar tabela: {e}")
            raise

def create_formularios_table():
    """Cria a tabela Formularios com GSI baseado no dynamo_stack.py"""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': envs.dynamo_partition_key,
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': envs.dynamo_sort_key,
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': envs.dynamo_partition_key,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': envs.dynamo_sort_key,
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI1PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI1SK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI2PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI2SK',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserPriorityIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'GSI1PK',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'GSI1SK',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'SystemUpdatedAtIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'GSI2PK',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'GSI2SK',
                            'KeyType': 'RANGE'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PROVISIONED',
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            StreamSpecification={
                'StreamEnabled': True,
                'StreamViewType': 'NEW_IMAGE'
            }
        )
        
        # Aguarda a tabela ser criada
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"✅ Tabela '{table_name}' criada com sucesso!")
        print("   - Partition Key: PK (String)")
        print("   - Sort Key: SK (String)")
        print("   - GSI: UserPriorityIndex (GSI1PK, GSI1SK)")
        print("   - GSI: SystemUpdatedAtIndex (GSI2PK, GSI2SK)")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Tabela '{table_name}' já existe")
        else:
            print(f"❌ Erro ao criar tabela: {e}")
            raise

def list_tables():
    """Lista todas as tabelas existentes"""
    response = client.list_tables()
    print(f"\n📋 Tabelas disponíveis: {response['TableNames']}")

def main():
    parser = argparse.ArgumentParser(
        description="Cria a tabela do DynamoDB local com GSIs esperadas pela aplicação."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Deleta e recria a tabela antes de criar os índices.",
    )
    args = parser.parse_args()

    print("🚀 Preparando estrutura do DynamoDB Local...\n")

    if args.reset:
        delete_table(table_name)

    create_formularios_table()
    list_tables()
    print("\n✨ Estrutura criada com sucesso! Acesse http://localhost:8001 para visualizar")

if __name__ == "__main__":
    main()
