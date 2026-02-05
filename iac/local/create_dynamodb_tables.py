#!/usr/bin/env python3
"""
Script para criar as tabelas DynamoDB localmente baseado na estrutura do CDK
"""
import boto3
from botocore.exceptions import ClientError

# Configuração do DynamoDB Local
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='sa-east-1',
    aws_access_key_id='local',
    aws_secret_access_key='local'
)

def delete_table(table_name):
    """Deleta uma tabela do DynamoDB Local"""
    try:
        client = boto3.client(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='sa-east-1',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
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
            TableName='Formularios_Table',
            KeySchema=[
                {
                    'AttributeName': 'PK',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'SK',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'SK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI1PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'GSI1SK',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
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
        table.meta.client.get_waiter('table_exists').wait(TableName='Formularios_Table')
        print(f"✅ Tabela 'Formularios_Table' criada com sucesso!")
        print(f"   - Partition Key: PK (String)")
        print(f"   - Sort Key: SK (String)")
        print(f"   - GSI: GSI1 (GSI1PK, GSI1SK)")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠️  Tabela 'Formularios_Table' já existe")
        else:
            print(f"❌ Erro ao criar tabela: {e}")
            raise

def list_tables():
    """Lista todas as tabelas existentes"""
    client = boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='sa-east-1',
        aws_access_key_id='local',
        aws_secret_access_key='local'
    )
    
    response = client.list_tables()
    print(f"\n📋 Tabelas disponíveis: {response['TableNames']}")

def main():
    print("🚀 Recriando estrutura do DynamoDB Local...\n")
    
    # Cria a tabela com o índice correto
    create_formularios_table()
    list_tables()
    print("\n✨ Estrutura criada com sucesso! Acesse http://localhost:8001 para visualizar")

if __name__ == "__main__":
    main()
