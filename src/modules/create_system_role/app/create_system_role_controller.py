from pydantic import ValidationError

from .create_system_role_usecase import CreateSystemRoleUsecase
from .create_system_role_viewmodel import CreateSystemRoleViewmodel
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.contracts.runtime_requests import CreateSystemRoleControllerRequestSchema
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, Created, Forbidden, NotFound
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class CreateSystemRoleController:
    def __init__(self, usecase: CreateSystemRoleUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = CreateSystemRoleControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            result = self.usecase(
                requester_user_id=requester_user.user_id,
                system=payload.system,
                name=payload.name,
                actions=[Action(value) for value in payload.actions],
                is_default=payload.is_default,
            )

            viewmodel = CreateSystemRoleViewmodel(result)
            return Created(viewmodel.to_dict())

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
