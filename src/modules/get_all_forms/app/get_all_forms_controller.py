from .get_all_forms_usecase import GetAllFormsUsecase
from .get_all_forms_viewmodel import GetAllFormsViewmodel
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, InternalServerError, NotFound, OK
from src.shared.infra.dtos.user_gateway import UserGatewayDTO
from src.shared.helpers.functions.pagination_token import decode_pagination_token


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
            if isinstance(value, bool) or not isinstance(value, int):
                raise WrongTypeParameter(field, "int", type(value))
            return value

        def _parse_optional_str(field: str, value):
            if value is None:
                return None
            if not isinstance(value, str):
                raise WrongTypeParameter(field, "str", type(value))
            return value

        limit = _parse_optional_int("limit", data.get("limit"), default=20)
        if limit < 1 or limit > 100:
            raise EntityError("limit")

        status = None
        status_raw = data.get("status")
        if status_raw is not None:
            if not isinstance(status_raw, str):
                raise WrongTypeParameter("status", "str", type(status_raw))
            status_str = status_raw.upper()
            if status_str not in FORM_STATUS.__members__:
                raise EntityError("status")
            status = FORM_STATUS[status_str]

        system = _parse_optional_str("system", data.get("system"))
        search = _parse_optional_str("search", data.get("search"))
        created_at_start = _parse_optional_int("created_at_start", data.get("created_at_start"))
        created_at_end = _parse_optional_int("created_at_end", data.get("created_at_end"))

        exclusive_start_key_field = "exclusive_start_key"
        exclusive_start_key_raw = data.get("exclusive_start_key")
        if exclusive_start_key_raw is None and "exclusiveStartKey" in data:
            exclusive_start_key_raw = data.get("exclusiveStartKey")
            exclusive_start_key_field = "exclusiveStartKey"

        if exclusive_start_key_raw is None:
            exclusive_start_key = None
        else:
            if not isinstance(exclusive_start_key_raw, str):
                raise WrongTypeParameter(exclusive_start_key_field, "str", type(exclusive_start_key_raw))
            try:
                decode_pagination_token(exclusive_start_key_raw)
            except ValueError:
                raise EntityError(exclusive_start_key_field)
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
                requester_user_id=requester_user.user_id,
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
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        except Exception as err:
            return InternalServerError(body=err.args[0])
