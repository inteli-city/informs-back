from pydantic import ValidationError

from .get_app_config_usecase import GetAppConfigUsecase
from .get_app_config_viewmodel import GetAppConfigViewmodel
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.contracts.runtime_requests import GetAppConfigControllerRequestSchema
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, InternalServerError, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAppConfigController:
    def __init__(self, usecase: GetAppConfigUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = GetAppConfigControllerRequestSchema.model_validate(data)
            requester = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            result = self.usecase(requester=requester)

            viewmodel = GetAppConfigViewmodel(result)
            return OK(viewmodel.to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))

        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except WrongTypeParameter as err:
            return BadRequest(body=err.message)
        except EntityError as err:
            # A configuração guardada é validada ao gravar; inválida aqui é
            # dado corrompido no banco, não erro de quem pediu.
            return InternalServerError(body=f"Configuração da aplicação inválida: {err.message}")
