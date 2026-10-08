from pydantic import ValidationError

from .put_system_app_config_usecase import PutSystemAppConfigUsecase
from .put_system_app_config_viewmodel import PutSystemAppConfigViewmodel
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.contracts.runtime_requests import PutSystemAppConfigControllerRequestSchema
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, Forbidden, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class PutSystemAppConfigController:
    def __init__(self, usecase: PutSystemAppConfigUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = PutSystemAppConfigControllerRequestSchema.model_validate(data)
            requester = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            result = self.usecase(requester=requester, system=payload.system, values=payload.values, base_version=payload.base_version)

            return OK(PutSystemAppConfigViewmodel(result).to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))
        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        except DuplicatedItem as err:
            return Conflict(body=err.message)
        except EntityError as err:
            return BadRequest(body=err.message)
