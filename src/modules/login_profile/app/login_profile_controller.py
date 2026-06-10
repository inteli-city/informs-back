from pydantic import ValidationError

from .login_profile_usecase import LoginProfileUsecase
from .login_profile_viewmodel import LoginProfileViewmodel
from src.shared.helpers.contracts.runtime_requests import LoginProfileControllerRequestSchema
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, Forbidden, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class LoginProfileController:
    def __init__(self, usecase: LoginProfileUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = LoginProfileControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            profile, just_created = self.usecase(
                user_id=requester_user.user_id,
                name=requester_user.name,
                email=requester_user.email,
                cognito_systems=requester_user.systems,
            )

            viewmodel = LoginProfileViewmodel(profile=profile, just_created=just_created)
            return OK(viewmodel.to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))
        except DuplicatedItem as err:
            # Pode acontecer em corrida entre dois logins simultâneos do
            # mesmo user. Retornar 409 dá ao client a chance de retry.
            return Conflict(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        except WrongTypeParameter as err:
            return BadRequest(body=err.message)
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
