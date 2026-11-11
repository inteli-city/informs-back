from .reverse_geocode_controller import ReverseGeocodeController
from .reverse_geocode_usecase import ReverseGeocodeUsecase
from src.shared.environments import Environments
from src.shared.helpers.error_handler import lambda_error_handler
from src.shared.helpers.logging_handler import lambda_logging_handler
from src.shared.helpers.external_interfaces.http_lambda_requests import LambdaHttpRequest, LambdaHttpResponse


geocoder = Environments.get_reverse_geocoder()
usecase = ReverseGeocodeUsecase(geocoder)
controller = ReverseGeocodeController(usecase)


@lambda_logging_handler
@lambda_error_handler
def lambda_handler(event, context):
    http_request = LambdaHttpRequest(data=event)
    http_request.data["requester_user"] = event.get("requestContext", {}).get("authorizer", {}).get("claims", None)
    response = controller(http_request)
    http_response = LambdaHttpResponse(status_code=response.status_code, body=response.body, headers=response.headers)
    return http_response.toDict()
