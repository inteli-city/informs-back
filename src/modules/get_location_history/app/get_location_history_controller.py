from pydantic import ValidationError

from .get_location_history_usecase import GetLocationHistoryUsecase
from .get_location_history_viewmodel import GetLocationHistoryViewmodel
from src.shared.helpers.contracts.runtime_requests import (
    GetLocationHistoryControllerRequestSchema,
)
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.errors.controller_errors import (
    MissingParameters,
    WrongTypeParameter,
)
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import (
    IRequest,
    IResponse,
)
from src.shared.helpers.external_interfaces.http_codes import (
    BadRequest,
    Forbidden,
    NotFound,
    OK,
)
from src.shared.helpers.functions.pydantic_error_parser import (
    get_validation_error_message,
)
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetLocationHistoryController:
    def __init__(self, usecase: GetLocationHistoryUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = GetLocationHistoryControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(
                payload.requester_user.model_dump(by_alias=True)
            )

            pings = self.usecase(
                requester_user_id=requester_user.user_id,
                target_user_id=payload.user_id,
                since_ms=payload.since,
                until_ms=payload.until,
            )

            viewmodel = GetLocationHistoryViewmodel(pings=pings)
            return OK(viewmodel.to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))
        except NoItemsFound as err:
            return NotFound(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        except WrongTypeParameter as err:
            return BadRequest(body=err.message)
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
