from .get_app_config_admin_controller import GetAppConfigAdminController
from .get_app_config_admin_usecase import GetAppConfigAdminUsecase
from src.shared.environments import Environments
from src.shared.helpers.error_handler import lambda_error_handler
from src.shared.helpers.logging_handler import lambda_logging_handler
from src.shared.helpers.external_interfaces.http_lambda_requests import LambdaHttpRequest, LambdaHttpResponse


profile_repo = Environments.get_profile_repo()
system_config_repo = Environments.get_system_config_repo()
usecase = GetAppConfigAdminUsecase(profile_repo, system_config_repo)
controller = GetAppConfigAdminController(usecase)


@lambda_logging_handler
@lambda_error_handler
def lambda_handler(event, context):
    http_request = LambdaHttpRequest(data=event)
    http_request.data["requester_user"] = event.get("requestContext", {}).get("authorizer", {}).get("claims", None)
    response = controller(http_request)
    http_response = LambdaHttpResponse(status_code=response.status_code, body=response.body, headers=response.headers)
    return http_response.toDict()
