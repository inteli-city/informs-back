from pydantic import ValidationError

from .create_profile_usecase import CreateProfileUsecase
from .create_profile_viewmodel import CreateProfileViewmodel
from src.shared.domain.enums.profile_role_enum import PROFILE_ROLE
from src.shared.helpers.contracts.runtime_requests import CreateProfileControllerRequestSchema
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, Created, Forbidden
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class CreateProfileController:
    def __init__(self, usecase: CreateProfileUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = CreateProfileControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            profile = self.usecase(
                requester_user_id=requester_user.user_id,
                target_user_id=payload.user_id,
                role=PROFILE_ROLE(payload.role),
                name=payload.name,
                email=payload.email,
                system=payload.system,
                vehicle_plate=payload.vehicle_plate,
            )

            viewmodel = CreateProfileViewmodel(profile=profile)
            return Created(viewmodel.to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))
        except DuplicatedItem as err:
            return Conflict(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        except WrongTypeParameter as err:
            return BadRequest(body=err.message)
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
