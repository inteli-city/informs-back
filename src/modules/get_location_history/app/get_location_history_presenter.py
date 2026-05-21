from .get_location_history_controller import GetLocationHistoryController
from .get_location_history_usecase import GetLocationHistoryUsecase
from src.shared.environments import Environments
from src.shared.helpers.error_handler import lambda_error_handler
from src.shared.helpers.logging_handler import lambda_logging_handler
from src.shared.helpers.external_interfaces.http_lambda_requests import (
    LambdaHttpRequest,
    LambdaHttpResponse,
)


location_repo = Environments.get_location_repo()
profile_repo = Environments.get_profile_repo()
usecase = GetLocationHistoryUsecase(location_repo=location_repo, profile_repo=profile_repo)
controller = GetLocationHistoryController(usecase)


@lambda_logging_handler
@lambda_error_handler
def lambda_handler(event, context):
    http_request = LambdaHttpRequest(data=event)
    http_request.data["requester_user"] = (
        event.get("requestContext", {}).get("authorizer", {}).get("claims", None)
    )
    response = controller(http_request)
    http_response = LambdaHttpResponse(
        status_code=response.status_code,
        body=response.body,
        headers=response.headers,
    )
    return http_response.toDict()
