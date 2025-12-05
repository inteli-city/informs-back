from aws_cdk import (
    aws_lambda as lambda_,
    Duration
)
from constructs import Construct
from aws_cdk.aws_apigateway import Resource, LambdaIntegration, CognitoUserPoolsAuthorizer


class LambdaStack(Construct):
    functions_that_need_dynamo_forms_permissions = []
    functions_that_need_cognito_permissions = []

    def create_lambda_api_gateway_integration(self, module_name: str, method: str, api_resource: Resource,
                                              environment_variables: dict = {"STAGE": "DEV"}, authorizer=None):

        function = lambda_.Function(
            self, module_name.title(),
            code=lambda_.Code.from_asset(f"../src/modules/{module_name}"),
            handler=f"app.{module_name}_presenter.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            layers=[self.lambda_layer],
            memory_size=512,
            environment=environment_variables,
            timeout=Duration.seconds(15)
        )

        api_resource.add_resource(module_name.replace("_", "-")).add_method(method,
                                                                                       integration=LambdaIntegration(
                                                                                           function),
                                                                                        authorizer=authorizer)

        return function

    def __init__(self, scope: Construct, api_gateway_resource: Resource, environment_variables: dict,
                 authorizer: CognitoUserPoolsAuthorizer) -> None:
        super().__init__(scope, "Formularios_Lambda")

        self.lambda_layer = lambda_.LayerVersion(self, "Formularios_Layer",
                                                 code=lambda_.Code.from_asset("./lambda_layer_out_temp"),
                                                 compatible_runtimes=[lambda_.Runtime.PYTHON_3_9]
                                                 )
        self.cancel_form = self.create_lambda_api_gateway_integration(
            module_name="cancel_form",
            method="POST",
            api_resource=api_gateway_resource,
            environment_variables=environment_variables,
            authorizer=authorizer
        )

        self.complete_form = self.create_lambda_api_gateway_integration(
            module_name="complete_form",
            method="POST",
            api_resource=api_gateway_resource,
            environment_variables=environment_variables,
            authorizer=authorizer
        )

        self.create_form = self.create_lambda_api_gateway_integration(
            module_name="create_form",
            method="POST",
            api_resource=api_gateway_resource,
            environment_variables=environment_variables,
            authorizer=authorizer
        )

        self.get_form = self.create_lambda_api_gateway_integration(
            module_name="get_form",
            method="GET",
            api_resource=api_gateway_resource,
            environment_variables=environment_variables,
            authorizer=authorizer
        )

        self.get_all_forms = self.create_lambda_api_gateway_integration(
            module_name="get_all_forms",
            method="GET",
            api_resource=api_gateway_resource,
            environment_variables=environment_variables,
            authorizer=authorizer
        )

        self.start_form = self.create_lambda_api_gateway_integration(
            module_name="start_form",
            method="POST",
            api_resource=api_gateway_resource,
            environment_variables=environment_variables,
            authorizer=authorizer
        )

        self.functions_that_need_dynamo_forms_permissions = [
            self.create_form,
            self.cancel_form,
            self.complete_form,
            self.get_all_forms,
            self.start_form,
            self.get_form
        ]

        self.functions_that_need_cognito_permissions = [
            self.create_form,
            self.cancel_form,
            self.complete_form,
            self.get_all_forms,
            self.start_form,
            self.get_form
        ]
