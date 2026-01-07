from .get_all_templates_usecase import GetAllTemplatesUsecase
from .get_all_templates_viewmodel import GetAllTemplatesViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, InvalidPaginationToken, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, InternalServerError, NotFound, OK
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAllTemplatesController:
    def __init__(self, usecase: GetAllTemplatesUsecase):
        self.usecase = usecase

    def _validate_requester_user(self, data: dict) -> UserGatewayDTO:
        requester_user = data.get("requester_user")
        if requester_user is None:
            raise MissingParameters("requester_user")
        return UserGatewayDTO.from_api_gateway(requester_user)

    def _validate_endpoint_parameters(self, data: dict):
        def _parse_optional_int(field: str, value, default=None):
            if value is None:
                return default
            if isinstance(value, bool):
                raise WrongTypeParameter(field, "int", type(value))
            if isinstance(value, str):
                if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                    return int(value)
                raise WrongTypeParameter(field, "int", type(value))
            if not isinstance(value, int):
                raise WrongTypeParameter(field, "int", type(value))
            return value

        limit = _parse_optional_int("limit", data.get("limit"), default=20)
        if limit < 1 or limit > 100:
            raise EntityError("limit")

        is_active_raw = data.get("is_active")
        is_active_field = "is_active"
        if is_active_raw is None:
            is_active_raw = True

        if not isinstance(is_active_raw, bool):
            raise WrongTypeParameter(is_active_field, "bool", type(is_active_raw))
        is_active = is_active_raw
        
        system = data.get("system")
        if system is None:
            raise MissingParameters("system")
        if not isinstance(system, str):
            raise WrongTypeParameter("system", "str", type(system))

        name_filter = data.get("name")
        if name_filter is not None and not isinstance(name_filter, str):
            raise WrongTypeParameter("name", "str", type(name_filter))

        exclusive_start_key_field = "exclusive_start_key"
        exclusive_start_key_raw = data.get("exclusive_start_key")

        if exclusive_start_key_raw is None:
            exclusive_start_key = None
        else:
            if not isinstance(exclusive_start_key_raw, str):
                raise WrongTypeParameter(exclusive_start_key_field, "str", type(exclusive_start_key_raw))
            exclusive_start_key = exclusive_start_key_raw

        return limit, is_active, system, name_filter, exclusive_start_key

    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            requester = self._validate_requester_user(data)
            limit, is_active, system, name_filter, exclusive_start_key = self._validate_endpoint_parameters(data)

            templates, next_key = self.usecase(
                requester=requester,
                system=system,
                limit=limit,
                exclusive_start_key=exclusive_start_key,
                name_contains=name_filter,
                is_active=is_active,
            )

            viewmodel = GetAllTemplatesViewmodel(templates=templates, limit=limit, last_evaluated_key=next_key, system=system)
            return OK(viewmodel.to_dict())

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
        except Exception as err:
            return InternalServerError(body=err.args[0] if err.args else str(err))
