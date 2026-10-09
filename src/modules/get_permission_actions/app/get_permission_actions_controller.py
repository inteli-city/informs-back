from pydantic import ValidationError

from .get_permission_actions_usecase import GetPermissionActionsUsecase
from .get_permission_actions_viewmodel import GetPermissionActionsViewmodel
from src.shared.helpers.contracts.runtime_requests import GetPermissionActionsControllerRequestSchema
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, OK, Forbidden, NotFound
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message


class GetPermissionActionsController:
    def __init__(self, usecase: GetPermissionActionsUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            # Só confere que veio de um usuário autenticado; o catálogo é o mesmo para todos.
            GetPermissionActionsControllerRequestSchema.model_validate(data)
            result = self.usecase()

            viewmodel = GetPermissionActionsViewmodel(result)
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
