from src.modules.create_template.app.create_template_controller import CreateTemplateController
from src.modules.create_template.app.create_template_usecase import CreateTemplateUsecase
from src.shared.environments import Environments
from src.shared.helpers.error_handler import lambda_error_handler
from src.shared.helpers.external_interfaces.http_lambda_requests import LambdaHttpRequest, LambdaHttpResponse


repo = Environments.get_template_repo()()
usecase = CreateTemplateUsecase(repo)
controller = CreateTemplateController(usecase)


@lambda_error_handler
def lambda_handler(event, context):
    httpRequest = LambdaHttpRequest(data=event)
    httpRequest.data["requester_user"] = event.get("requestContext", {}).get("authorizer", {}).get("claims", None)
    response = controller(httpRequest)
    httpResponse = LambdaHttpResponse(status_code=response.status_code, body=response.body, headers=response.headers)

    return httpResponse.toDict()
