from pydantic import ValidationError

from .update_profile_usecase import UpdateProfileUsecase
from .update_profile_viewmodel import UpdateProfileViewmodel
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.helpers.contracts.runtime_requests import UpdateProfileControllerRequestSchema
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, Forbidden, NotFound, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class UpdateProfileController:
    def __init__(self, usecase: UpdateProfileUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = UpdateProfileControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            profile = self.usecase(
                requester_user_id=requester_user.user_id,
                target_user_id=payload.user_id,
                role=ProfileRole(payload.role),
                scope=payload.scope,
            )

            viewmodel = UpdateProfileViewmodel(profile=profile)
            return OK(viewmodel.to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))
        except NoItemsFound as err:
            return NotFound(body=err.message)
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
