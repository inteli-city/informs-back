from .get_all_forms_usecase import GetAllFormsUsecase
from .get_all_forms_viewmodel import GetAllFormsViewmodel
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, InvalidPaginationToken, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, InternalServerError, NotFound, OK
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAllFormsController:
    def __init__(self, usecase: GetAllFormsUsecase):
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

        def _parse_optional_str(field: str, value):
            if value is None:
                return None
            if not isinstance(value, str):
                raise WrongTypeParameter(field, "str", type(value))
            return value

        def _parse_optional_str_list(field: str, value):
            if value is None:
                return None
            if isinstance(value, list):
                if not value:
                    return []
                if not all(isinstance(item, str) for item in value):
                    raise WrongTypeParameter(field, "list[str]", type(value))
                return value
            if isinstance(value, str):
                return [value]
            raise WrongTypeParameter(field, "list[str]", type(value))

        limit = _parse_optional_int("limit", data.get("limit"), default=None)
        if limit is not None and (limit < 1 or limit > 10000):
            raise EntityError("limit")

        status = None
        status_raw = data.get("status")
        if status_raw is not None:
            status_values = status_raw if isinstance(status_raw, list) else [status_raw]
            parsed_statuses = []
            for status_item in status_values:
                if not isinstance(status_item, str):
                    raise WrongTypeParameter("status", "str", type(status_item))
                status_str = status_item.upper()
                if status_str not in FORM_STATUS.__members__:
                    raise EntityError("status")
                parsed_statuses.append(FORM_STATUS[status_str])
            status = parsed_statuses[0] if len(parsed_statuses) == 1 else parsed_statuses

        system = _parse_optional_str_list("system", data.get("system"))
        search = _parse_optional_str("search", data.get("search"))
        created_at_start = _parse_optional_int("created_at_start", data.get("created_at_start"))
        created_at_end = _parse_optional_int("created_at_end", data.get("created_at_end"))

        exclusive_start_key_field = "exclusive_start_key"
        exclusive_start_key_raw = data.get("exclusive_start_key")

        if exclusive_start_key_raw is not None and not isinstance(exclusive_start_key_raw, str):
            raise WrongTypeParameter(exclusive_start_key_field, "str", type(exclusive_start_key_raw))
        
        exclusive_start_key = exclusive_start_key_raw

        return limit, status, system, search, created_at_start, created_at_end, exclusive_start_key

    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            requester_user = self._validate_requester_user(data)

            (
                limit,
                status,
                system,
                search,
                created_at_start,
                created_at_end,
                exclusive_start_key,
            ) = self._validate_endpoint_parameters(data)

            forms, next_key = self.usecase(
                requester=requester_user,
                limit=limit,
                exclusive_start_key=exclusive_start_key,
                status=status,
                system=system,
                created_at_start=created_at_start,
                created_at_end=created_at_end,
                search=search,
            )

            viewmodel = GetAllFormsViewmodel(forms=forms, limit=limit, last_evaluated_key=next_key)
            return OK(viewmodel.to_dict())

        except NoItemsFound as err:
            return NotFound(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except ForbiddenAction as err:
            return BadRequest(body=err.message)
        except WrongTypeParameter as err:
            return BadRequest(body=err.message)
        except InvalidPaginationToken as err:
            return BadRequest(body=err.message)
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        except Exception as err:
            return InternalServerError(body=err.args[0])
