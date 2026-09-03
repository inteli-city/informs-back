from aws_cdk import (
    aws_lambda as lambda_,
    Duration,
    aws_scheduler as scheduler,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct
from typing import Optional
from aws_cdk.aws_apigateway import IAuthorizer, Resource, LambdaIntegration, CognitoUserPoolsAuthorizer


class LambdaStack(Construct):
    functions_that_need_dynamo_forms_permissions = []
    functions_that_need_dynamo_profiles_permissions = []
    functions_that_need_cognito_permissions = []

    def create_lambda_api_gateway_integration(self, module_name: str, method: str, api_resource: Resource,
                                              path: str = None, environment_variables: dict = None, authorizer: Optional[IAuthorizer] = None):

        function = lambda_.Function(
            self, module_name.title(),
            code=lambda_.Code.from_asset(f"../src/modules/{module_name}"),
            handler=f"app.{module_name}_presenter.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_10,
            layers=[self.lambda_layer],
            memory_size=512,
            environment=environment_variables,
            timeout=Duration.seconds(15),
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        resource = api_resource
        if path is not None:
            for segment in [seg for seg in path.split("/") if seg]:
                resource = resource.add_resource(segment)

        resource.add_method(method, LambdaIntegration(function), authorizer=authorizer)

        return function

    def __init__(self, scope: Construct, api_gateway_resource: Resource, environment_variables: dict,
                 authorizer: Optional[IAuthorizer]) -> None:
        super().__init__(scope, "Formularios_Lambda")

        self.lambda_layer = lambda_.LayerVersion(self, "Formularios_Layer",
                                                 code=lambda_.Code.from_asset("./lambda_layer_out_temp"),
                                                 compatible_runtimes=[lambda_.Runtime.PYTHON_3_10]
                                                 )

        # O bucket não é gerenciado por este CDK (só referenciado por nome via
        # BUCKET_NAME), então toda permissão de S3 é concedida pelo ARN
        # construído aqui em vez de por bucket.grant_*().
        bucket_name = environment_variables.get("BUCKET_NAME")
        forms_resource = api_gateway_resource.add_resource("forms")
        form_id_resource = forms_resource.add_resource("{form_id}")
        templates_resource = api_gateway_resource.add_resource("templates")
        template_id_resource = templates_resource.add_resource("{template_id}")
        profiles_resource = api_gateway_resource.add_resource("profiles")
        profile_user_id_resource = profiles_resource.add_resource("{user_id}")
        locations_resource = api_gateway_resource.add_resource("locations")
        locations_history_resource = locations_resource.add_resource("history")
        docs_resource = api_gateway_resource.add_resource("docs")

        self.create_form = self.create_lambda_api_gateway_integration(
            module_name="create_form",
            method="POST",
            api_resource=forms_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.get_all_forms = self.create_lambda_api_gateway_integration(
            module_name="get_all_forms",
            method="GET",
            api_resource=forms_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.get_form = self.create_lambda_api_gateway_integration(
            module_name="get_form",
            method="GET",
            api_resource=form_id_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.start_form = self.create_lambda_api_gateway_integration(
            module_name="start_form",
            method="POST",
            api_resource=form_id_resource,
            path="start",
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.submit_form = self.create_lambda_api_gateway_integration(
            module_name="submit_form",
            method="POST",
            api_resource=form_id_resource,
            path="submit",
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.cancel_form = self.create_lambda_api_gateway_integration(
            module_name="cancel_form",
            method="POST",
            api_resource=form_id_resource,
            path="cancel",
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.refresh_presign = self.create_lambda_api_gateway_integration(
            module_name="refresh_presign",
            method="POST",
            api_resource=form_id_resource,
            path="files/refresh-presign",
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        # As 4 lambdas que assinam presigned URL de upload (create/submit/cancel
        # e a renovação) precisam de s3:PutObject na identidade que assina: quem
        # valida a permissão no PUT é o S3, contra a role de QUEM gerou a
        # assinatura — não importa de onde o cliente faça a requisição, então
        # isso nunca depende de IP de origem. Isto substitui a policy manual
        # "FormulariosProductionPresignedUploadS3Policy" (hoje só anexada a 3
        # das 4 roles em prod — o refresh_presign nunca a recebeu), trazendo a
        # permissão para o código versionado em vez de um estado manual na AWS.
        if bucket_name:
            s3_put_policy = iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:PutObject", "s3:PutObjectTagging", "s3:AbortMultipartUpload"],
                resources=[f"arn:aws:s3:::{bucket_name}/*"],
            )
            for lambda_fn in (self.create_form, self.submit_form, self.cancel_form, self.refresh_presign):
                lambda_fn.add_to_role_policy(s3_put_policy)

        self.plan_route = self.create_lambda_api_gateway_integration(
            module_name="plan_route",
            method="POST",
            api_resource=forms_resource,
            path="route-plan",
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.create_profile = self.create_lambda_api_gateway_integration(
            module_name="create_profile",
            method="POST",
            api_resource=profiles_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.login_profile = self.create_lambda_api_gateway_integration(
            module_name="login_profile",
            method="POST",
            api_resource=profiles_resource,
            path="login",
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.delete_profile = self.create_lambda_api_gateway_integration(
            module_name="delete_profile",
            method="DELETE",
            api_resource=profile_user_id_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.update_profile = self.create_lambda_api_gateway_integration(
            module_name="update_profile",
            method="PUT",
            api_resource=profile_user_id_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.get_location_history = self.create_lambda_api_gateway_integration(
            module_name="get_location_history",
            method="GET",
            api_resource=locations_history_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.create_template = self.create_lambda_api_gateway_integration(
            module_name="create_template",
            method="POST",
            api_resource=templates_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.update_template = self.create_lambda_api_gateway_integration(
            module_name="update_template",
            method="PUT",
            api_resource=template_id_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.get_template = self.create_lambda_api_gateway_integration(
            module_name="get_template",
            method="GET",
            api_resource=template_id_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.get_all_templates = self.create_lambda_api_gateway_integration(
            module_name="get_all_templates",
            method="GET",
            api_resource=templates_resource,
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.docs = self.create_lambda_api_gateway_integration(
            module_name="docs",
            method="GET",
            api_resource=docs_resource,
            environment_variables=environment_variables,
            authorizer=None,
        )

        self.sync_forms_origin_module_name = "sync_forms_origin"
        self.sync_forms_origin_callback_module_name = "sync_forms_origin_callback"

        self.sync_forms_origin = lambda_.Function(
            self,
            self.sync_forms_origin_module_name.title(),
            code=lambda_.Code.from_asset("../src/modules/sync_forms_origin"),
            handler="app.sync_forms_origin_presenter.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_10,
            layers=[self.lambda_layer],
            memory_size=512,
            environment=environment_variables,
            timeout=Duration.seconds(60),
            tracing=lambda_.Tracing.ACTIVE,
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        self.sync_forms_origin_callback = self.create_lambda_api_gateway_integration(
            module_name=self.sync_forms_origin_callback_module_name,
            method="POST",
            api_resource=forms_resource,
            path="sync-origin/callback",
            environment_variables=environment_variables,
            authorizer=authorizer,
        )

        self.sync_forms_origin_scheduler_role = iam.Role(
            self,
            "SyncFormsOriginSchedulerRole",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
        )
        self.sync_forms_origin.grant_invoke(self.sync_forms_origin_scheduler_role)

        self.sync_forms_origin_schedule = scheduler.CfnSchedule(
            self,
            "SyncFormsOriginEventBridgeScheduler",
            schedule_expression="rate(5 minutes)",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF",
            ),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.sync_forms_origin.function_arn,
                role_arn=self.sync_forms_origin_scheduler_role.role_arn,
                input='{"trigger":"eventbridge-scheduler","job":"sync_forms_origin"}',
            ),
            description="Runs sync_forms_origin every 5 minutes",
            state="ENABLED",
        )

        self.reconcile_form_files_module_name = "reconcile_form_files"

        self.reconcile_form_files = lambda_.Function(
            self,
            self.reconcile_form_files_module_name.title(),
            code=lambda_.Code.from_asset("../src/modules/reconcile_form_files"),
            handler="app.reconcile_form_files_presenter.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_10,
            layers=[self.lambda_layer],
            memory_size=512,
            environment=environment_variables,
            # Um LIST por formulário: a janela de 24h cabe folgada em 5 min, e o
            # backfill histórico é invocado manualmente com janela fatiada.
            timeout=Duration.seconds(300),
            tracing=lambda_.Tracing.ACTIVE,
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        if bucket_name:
            self.reconcile_form_files.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["s3:ListBucket"],
                    resources=[f"arn:aws:s3:::{bucket_name}"],
                )
            )
            self.reconcile_form_files.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["s3:GetObject"],
                    resources=[f"arn:aws:s3:::{bucket_name}/*"],
                )
            )

        self.reconcile_form_files_scheduler_role = iam.Role(
            self,
            "ReconcileFormFilesSchedulerRole",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
        )
        self.reconcile_form_files.grant_invoke(self.reconcile_form_files_scheduler_role)

        self.reconcile_form_files_schedule = scheduler.CfnSchedule(
            self,
            "ReconcileFormFilesEventBridgeScheduler",
            schedule_expression="rate(1 hour)",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF",
            ),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.reconcile_form_files.function_arn,
                role_arn=self.reconcile_form_files_scheduler_role.role_arn,
                input='{"trigger":"eventbridge-scheduler","job":"reconcile_form_files"}',
            ),
            description="Reconciles form files against S3 every hour",
            state="ENABLED",
        )

        # Notificação não passa mais por CloudWatch Alarm + SNS: o
        # reconcile_form_files_presenter empurra 2 pushes HTTP pro Kuma
        # (heartbeat sempre; missing-files up/down) via KUMA_HEARTBEAT_PUSH_URL
        # e KUMA_MISSING_FILES_PUSH_URL em environment_variables — é o Kuma quem
        # decide notificar o Teams, mesmo padrão já usado para outros serviços.
        # A métrica FormsWithMissingFiles continua sendo emitida (ver
        # presenter) só para dashboard/debug no CloudWatch.

        self.functions_that_need_dynamo_forms_permissions = [
            self.refresh_presign,
            self.create_form,
            self.cancel_form,
            self.submit_form,
            self.get_all_forms,
            self.start_form,
            self.get_form,
            self.create_template,
            self.update_template,
            self.get_template,
            self.get_all_templates,
            self.plan_route,
            self.sync_forms_origin,
            self.sync_forms_origin_callback,
        ]
        # A reconciliação só pode consultar o GSI2 por sistema e janela. Não
        # recebe grant_read_data/read_write_data porque esses grants incluem
        # dynamodb:Scan, incompatível com o custo esperado desse scheduler.
        self.functions_that_need_dynamo_forms_gsi2_query_permissions = [
            self.reconcile_form_files,
        ]

        self.functions_that_need_cognito_permissions = [
            self.refresh_presign,
            self.create_form,
            self.cancel_form,
            self.submit_form,
            self.get_all_forms,
            self.start_form,
            self.get_form,
            self.create_template,
            self.update_template,
            self.get_template,
            self.get_all_templates,
            self.plan_route,
        ]

        self.functions_that_need_dynamo_profiles_permissions = [
            self.create_profile,
            self.login_profile,
            self.delete_profile,
            self.update_profile,
            self.get_location_history,
        ]

        # Lambdas que precisam ler a tabela Location (provisionada na
        # FormulariosTrackingStack — stack separada). IacStack atribui
        # permissão via wildcard ARN.
        self.functions_that_need_dynamo_location_read_permissions = [
            self.get_location_history,
        ]
