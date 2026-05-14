"""
FormulariosTrackingStack — infra DynamoDB pro tracking realtime.

Após migração do WS server pra Railway (sem Lightsail), esta stack
provisiona APENAS as 3 tabelas Location (uma por env). O servidor
WebSocket roda no Railway e escreve aqui via boto3 + access key (env
var AWS_ACCESS_KEY_ID/SECRET configurada no Railway).

A Lambda REST `/mss-formularios/locations/history` (PR #50) também
consome estas tabelas — daí o nome continua sendo importado via
`Fn.import_value` no IacStack.

Resources criados:
- 3× DynamoDB Table (Location dev/homolog/prod), nomes auto-gerados
  pelo CFN (FormulariosTrackingStack-LocationTable{stage}-...).
"""

import os
from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_dynamodb,
)
from constructs import Construct


# Stages cobertos pela mesma stack (1 deploy provisiona as 3 tabelas).
STAGES = ("dev", "homolog", "prod")


class FormulariosTrackingStack(Stack):
    """Stack independente — só DDB Location, sem Lightsail/IAM."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        github_ref_name = os.environ.get("GITHUB_REF_NAME", "dev")
        # Em prod retemos tabelas; demais envs destroem junto com a stack.
        removal_policy = (
            RemovalPolicy.RETAIN if "prod" in github_ref_name else RemovalPolicy.DESTROY
        )

        # ---------- Location tables (uma por stage) ----------
        # Schema:
        #   PK = user#{user_id}
        #   SK = ts#{epoch_ms}        (sortável cronologicamente)
        # Atributos: lat (N), lng (N), accuracy (N opc), ts_device (N opc).
        # Sem TTL: histórico completo retido por decisão do produto.
        # SEM table_name explícito: nome físico segue padrão da stack
        # (FormulariosTrackingStack-LocationTable{stage}-...). Consumidores
        # (Railway WS server, Lambda /locations/history) descobrem o nome via
        # CFN Output ou Fn.import_value.
        self.location_tables: dict[str, aws_dynamodb.Table] = {}
        for stage in STAGES:
            table = aws_dynamodb.Table(
                self,
                f"Location_Table_{stage}",
                partition_key=aws_dynamodb.Attribute(
                    name="PK", type=aws_dynamodb.AttributeType.STRING
                ),
                sort_key=aws_dynamodb.Attribute(
                    name="SK", type=aws_dynamodb.AttributeType.STRING
                ),
                billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
                point_in_time_recovery=True,
                # Em prod: RETAIN. Outros envs: DESTROY (recriam fácil).
                removal_policy=(
                    RemovalPolicy.RETAIN if stage == "prod" else removal_policy
                ),
            )
            self.location_tables[stage] = table
            CfnOutput(
                self,
                f"LocationTableName_{stage}",
                value=table.table_name,
                export_name=f"FormulariosTrackingLocationTable{stage}",
            )
