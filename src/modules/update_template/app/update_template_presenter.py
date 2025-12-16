from src.modules.update_template.app.update_template_controller import UpdateTemplateController
from src.modules.update_template.app.update_template_usecase import UpdateTemplateUsecase
from src.shared.environments import Environments
from src.shared.helpers.error_handler import lambda_error_handler
from src.shared.helpers.external_interfaces.http_lambda_requests import LambdaHttpRequest, LambdaHttpResponse


repo = Environments.get_template_repo()()
usecase = UpdateTemplateUsecase(repo)
controller = UpdateTemplateController(usecase)


@lambda_error_handler
def lambda_handler(event, context):
    httpRequest = LambdaHttpRequest(data=event)
    httpRequest.data["requester_user"] = event.get("requestContext", {}).get("authorizer", {}).get("claims", None)
    path_template_id = event.get("pathParameters", {}).get("templateId") if event.get("pathParameters") else None
    if path_template_id:
        httpRequest.data["template_id"] = path_template_id
    response = controller(httpRequest)
    httpResponse = LambdaHttpResponse(status_code=response.status_code, body=response.body, headers=response.headers)

    return httpResponse.toDict()
