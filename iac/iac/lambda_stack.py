from aws_cdk import (
    aws_lambda as lambda_,
    Duration,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
)
from constructs import Construct
from aws_cdk.aws_apigateway import Resource, LambdaIntegration, CognitoUserPoolsAuthorizer


class LambdaStack(Construct):
    functions_that_need_dynamo_forms_permissions = []
    functions_that_need_cognito_permissions = []

    def create_lambda_api_gateway_integration(self, module_name: str, method: str, api_resource: Resource,
                                              path: str = None, environment_variables: dict = {"STAGE": "DEV"}, authorizer=None):

        function = lambda_.Function(
            self, module_name.title(),
            code=lambda_.Code.from_asset(f"../src/modules/{module_name}"),
            handler=f"app.{module_name}_presenter.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
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
                 authorizer: CognitoUserPoolsAuthorizer) -> None:
        super().__init__(scope, "Formularios_Lambda")

        self.lambda_layer = lambda_.LayerVersion(self, "Formularios_Layer",
                                                 code=lambda_.Code.from_asset("./lambda_layer_out_temp"),
                                                 compatible_runtimes=[lambda_.Runtime.PYTHON_3_9]
                                                 )
        forms_resource = api_gateway_resource.add_resource("forms")
        form_id_resource = forms_resource.add_resource("{form_id}")
        templates_resource = api_gateway_resource.add_resource("templates")
        template_id_resource = templates_resource.add_resource("{template_id}")
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

        self.sync_forms_origin = lambda_.Function(
            self,
            self.sync_forms_origin_module_name.title(),
            code=lambda_.Code.from_asset("../src/modules/sync_forms_origin"),
            handler="app.sync_forms_origin_presenter.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            layers=[self.lambda_layer],
            memory_size=512,
            environment=environment_variables,
            timeout=Duration.seconds(60),
            tracing=lambda_.Tracing.ACTIVE,
            log_retention=logs.RetentionDays.ONE_MONTH,
        )

        self.sync_forms_origin_rule = events.Rule(
            self,
            "SyncFormsOriginSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
        )
        self.sync_forms_origin_rule.add_target(
            targets.LambdaFunction(self.sync_forms_origin)
        )

        self.functions_that_need_dynamo_forms_permissions = [
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
            self.sync_forms_origin,
        ]

        self.functions_that_need_cognito_permissions = [
            self.create_form,
            self.cancel_form,
            self.submit_form,
            self.get_all_forms,
            self.start_form,
            self.get_form,
            self.create_template,
            self.update_template,
            self.get_template,
            self.get_all_templates
        ]
