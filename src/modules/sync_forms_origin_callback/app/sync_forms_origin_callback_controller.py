from datetime import datetime, timezone

from pydantic import ValidationError

from .sync_forms_origin_callback_usecase import SyncFormsOriginCallbackUsecase
from .sync_forms_origin_callback_viewmodel import SyncFormsOriginCallbackViewmodel
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.contracts.endpoints.sync_origin_callback_contract import SyncCallbackRequestSchema
from src.shared.helpers.errors.usecase_errors import NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, NotFound, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message


class SyncFormsOriginCallbackController:
    def __init__(self, usecase: SyncFormsOriginCallbackUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = SyncCallbackRequestSchema.model_validate(data)
            form_ids = payload.form_ids
            execution_id = payload.execution_id
            received_at = int(datetime.now(timezone.utc).timestamp() * 1000)
            saved_error_forms = self.usecase(
                form_ids=form_ids,
                received_at=received_at,
            )
            viewmodel = SyncFormsOriginCallbackViewmodel(
                form_ids=form_ids,
                saved_error_forms=saved_error_forms,
                received_at=received_at,
                execution_id=execution_id,
            )

            return OK(viewmodel.to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))

        except NoItemsFound as err:
            return NotFound(body=err.message)
