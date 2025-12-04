import os
from aws_cdk import (
    CfnOutput,
    aws_dynamodb,
    RemovalPolicy,
)
from constructs import Construct
from aws_cdk.aws_apigateway import Resource, LambdaIntegration

class DynamoStack(Construct):

        def __init__(self, scope: Construct) -> None:
            super().__init__(scope, "Formularios_Dynamo")

            self.github_ref_name = os.environ.get("GITHUB_REF_NAME")

            REMOVAL_POLICY = RemovalPolicy.RETAIN if 'prod' in self.github_ref_name else RemovalPolicy.DESTROY

            self.dynamo_table_forms = aws_dynamodb.Table(
                self, "Formularios_Table",
                partition_key=aws_dynamodb.Attribute(
                    name="PK",
                    type=aws_dynamodb.AttributeType.STRING
                ),
                sort_key=aws_dynamodb.Attribute(
                    name="SK",
                    type=aws_dynamodb.AttributeType.STRING
                ),
                point_in_time_recovery=True,
                billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
                removal_policy=REMOVAL_POLICY,
                stream=aws_dynamodb.StreamViewType.NEW_IMAGE,
                time_to_live_attribute="TTL"
            )

            self.gsi_user_priority = self.dynamo_table_forms.add_global_secondary_index(
                index_name="UserPriorityIndex",
                partition_key=aws_dynamodb.Attribute(
                    name="GSI1PK",
                    type=aws_dynamodb.AttributeType.STRING
                ),
                sort_key=aws_dynamodb.Attribute(
                    name="GSI1SK",
                    type=aws_dynamodb.AttributeType.STRING
                ),
                projection_type=aws_dynamodb.ProjectionType.ALL
            )

            CfnOutput(self, 'DynamoFormulariosRemovalPolicy',
                        value=REMOVAL_POLICY.value,
                        export_name=f'Formularios{self.github_ref_name}DynamoRemovalPolicyValue')