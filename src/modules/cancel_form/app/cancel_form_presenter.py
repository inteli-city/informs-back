from .cancel_form_controller import CancelFormController
from .cancel_form_usecase import CancelFormUsecase
from src.shared.environments import Environments
from src.shared.helpers.external_interfaces.http_lambda_requests import LambdaHttpRequest, LambdaHttpResponse


repo = Environments.get_form_repo()
file_repo = Environments.get_file_repo()
usecase = CancelFormUsecase(repo, file_repo)
controller = CancelFormController(usecase)

def lambda_handler(event, context):
    
    httpRequest = LambdaHttpRequest(data=event)
    httpRequest.data['requester_user'] = event.get('requestContext', {}).get('authorizer', {}).get('claims', None)
    response = controller(httpRequest)
    httpResponse = LambdaHttpResponse(status_code=response.status_code, body=response.body, headers=response.headers)
    
    return httpResponse.toDict()
