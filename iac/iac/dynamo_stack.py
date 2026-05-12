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

            self.gsi_system_updated_at = self.dynamo_table_forms.add_global_secondary_index(
                index_name="SystemUpdatedAtIndex",
                partition_key=aws_dynamodb.Attribute(
                    name="GSI2PK",
                    type=aws_dynamodb.AttributeType.STRING
                ),
                sort_key=aws_dynamodb.Attribute(
                    name="GSI2SK",
                    type=aws_dynamodb.AttributeType.STRING
                ),
                projection_type=aws_dynamodb.ProjectionType.ALL
            )

            CfnOutput(self, 'DynamoFormulariosRemovalPolicy',
                        value=REMOVAL_POLICY.value,
                        export_name=f'Formularios{self.github_ref_name}DynamoRemovalPolicyValue')

            # Tabela de Profiles (RBAC interno: ADMIN / INSPECTOR).
            # Cognito autentica; esta tabela controla a role aplicacional.
            # PK: user#{user_id} | SK: METADATA
            # GSI ByRole: PK role#{role}, SK system#{system}#user#{user_id}
            #   Uso atual: contar admins ativos antes de DELETE (impede
            #   remoção do último admin). Permite no futuro listar perfis.
            self.dynamo_table_profiles = aws_dynamodb.Table(
                self, "Profiles_Table",
                table_name=f"informs-tracking-profile-{self.github_ref_name}",
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
            )

            self.gsi_profiles_by_role = self.dynamo_table_profiles.add_global_secondary_index(
                index_name="ByRole",
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

            CfnOutput(self, 'DynamoProfilesRemovalPolicy',
                        value=REMOVAL_POLICY.value,
                        export_name=f'Profiles{self.github_ref_name}DynamoRemovalPolicyValue')