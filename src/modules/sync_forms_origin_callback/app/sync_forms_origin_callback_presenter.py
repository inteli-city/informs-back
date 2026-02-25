from aws_lambda_powertools import Logger

from .sync_forms_origin_callback_controller import SyncFormsOriginCallbackController
from .sync_forms_origin_callback_usecase import SyncFormsOriginCallbackUsecase
from src.shared.environments import Environments
from src.shared.helpers.external_interfaces.http_lambda_requests import LambdaHttpRequest, LambdaHttpResponse


SERVICE_NAME = "sync_forms_origin_callback"

logger = Logger(service=SERVICE_NAME)
usecase = SyncFormsOriginCallbackUsecase(
    form_repo=Environments.get_form_repo(),
    sync_error_form_repo=Environments.get_sync_error_form_repo(),
)
controller = SyncFormsOriginCallbackController(usecase=usecase)


@logger.inject_lambda_context(clear_state=True)
def lambda_handler(event, context):
    http_request = LambdaHttpRequest(data=event)
    response = controller(http_request)

    if response.status_code < 400:
        saved_error_forms = response.body.get("saved_error_forms", [])
        systems = sorted({item.get("system") for item in saved_error_forms if isinstance(item, dict) and item.get("system")})
        logger.info(
            "sync callback accepted",
            extra={
                "received_count": response.body.get("received_count", 0),
                "saved_count": len(saved_error_forms),
                "systems": systems,
                "execution_id": response.body.get("execution_id"),
            },
        )
    else:
        logger.warning(
            "sync callback rejected",
            extra={
                "status_code": response.status_code,
                "body": response.body,
            },
        )

    return LambdaHttpResponse(
        status_code=response.status_code,
        body=response.body,
        headers=response.headers,
    ).toDict()
