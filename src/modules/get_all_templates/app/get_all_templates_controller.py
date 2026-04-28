from pydantic import ValidationError

from .get_all_templates_usecase import GetAllTemplatesUsecase
from .get_all_templates_viewmodel import GetAllTemplatesViewmodel
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.contracts.runtime_requests import GetAllTemplatesControllerRequestSchema
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, InvalidPaginationToken, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, NotFound, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAllTemplatesController:
    def __init__(self, usecase: GetAllTemplatesUsecase):
        self.usecase = usecase
        self.expected_list_str = "list[str]"

    def _validate_endpoint_parameters(self, payload: GetAllTemplatesControllerRequestSchema):
        limit = payload.limit
        if limit is not None and (limit < 1 or limit > 10000):
            raise EntityError(f"Parâmetro 'limit' deve ser um número entre 1 e 10000, recebido: {limit}")

        is_active_raw = payload.is_active

        if is_active_raw is None:
            is_active = None if limit is None else True
        else:
            is_active = is_active_raw

        system_raw = payload.system
        if system_raw is None:
            system = None
        elif isinstance(system_raw, list):
            if not all(isinstance(item, str) for item in system_raw):
                raise WrongTypeParameter("system", self.expected_list_str, type(system_raw))
            system = system_raw
        elif isinstance(system_raw, str):
            system = [system_raw]
        else:
            raise WrongTypeParameter("system", self.expected_list_str, type(system_raw))

        return limit, is_active, system, payload.name, payload.exclusive_start_key

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = GetAllTemplatesControllerRequestSchema.model_validate(data)
            requester = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))
            limit, is_active, system, name_filter, exclusive_start_key = self._validate_endpoint_parameters(payload)

            templates, next_key = self.usecase(
                requester=requester,
                systems=system,
                limit=limit,
                exclusive_start_key=exclusive_start_key,
                name_contains=name_filter,
                is_active=is_active,
            )

            systems_used = system if system is not None else requester.systems
            viewmodel = GetAllTemplatesViewmodel(
                templates=templates,
                limit=limit,
                last_evaluated_key=next_key,
                systems=systems_used,
            )
            return OK(viewmodel.to_dict())

        except ValidationError as err:
            if isinstance(data.get("system"), int):
                return BadRequest(body=WrongTypeParameter("system", self.expected_list_str, type(data.get("system"))).message)
            return BadRequest(body=get_validation_error_message(err))
        except NoItemsFound as err:
            return NotFound(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        except WrongTypeParameter as err:
            return BadRequest(body=err.message)
        except InvalidPaginationToken as err:
            return BadRequest(body=err.message)
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
