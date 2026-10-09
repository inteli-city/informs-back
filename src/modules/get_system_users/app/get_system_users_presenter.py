from .get_system_users_controller import GetSystemUsersController
from .get_system_users_usecase import GetSystemUsersUsecase
from src.shared.domain.services.access_control import AccessControl
from src.shared.environments import Environments
from src.shared.helpers.error_handler import lambda_error_handler
from src.shared.helpers.logging_handler import lambda_logging_handler
from src.shared.helpers.external_interfaces.http_lambda_requests import LambdaHttpRequest, LambdaHttpResponse


profile_repo = Environments.get_profile_repo()
role_repo = Environments.get_system_role_repo()
access_control = AccessControl(profile_repo, role_repo)
usecase = GetSystemUsersUsecase(access_control, profile_repo, role_repo)
controller = GetSystemUsersController(usecase)


@lambda_logging_handler
@lambda_error_handler
def lambda_handler(event, context):
    http_request = LambdaHttpRequest(data=event)
    http_request.data['requester_user'] = event.get('requestContext', {}).get('authorizer', {}).get('claims', None)
    response = controller(http_request)
    http_response = LambdaHttpResponse(status_code=response.status_code, body=response.body, headers=response.headers)
    return http_response.toDict()
