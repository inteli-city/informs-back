import json
from typing import Optional

from .get_all_templates_usecase import GetAllTemplatesUsecase
from .get_all_templates_viewmodel import GetAllTemplatesViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, InternalServerError, NotFound, OK
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAllTemplatesController:
    def __init__(self, usecase: GetAllTemplatesUsecase):
        self.usecase = usecase

    def _parse_int(self, value: Optional[str], field_name: str) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            raise EntityError(field_name)

    def _parse_bool(self, value: Optional[str], field_name: str) -> Optional[bool]:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in ("true", "1"):
                return True
            if lowered in ("false", "0"):
                return False
        raise EntityError(field_name)

    def _parse_last_key(self, value: Optional[dict]) -> Optional[dict]:
        if value is None:
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                raise EntityError("last_evaluated_key")
        if not isinstance(value, dict):
            raise EntityError("last_evaluated_key")
        return value

    def _get_requester(self, data: dict) -> UserGatewayDTO:
        requester_user = data.get("requester_user")
        if requester_user is None:
            raise MissingParameters("requester_user")
        return UserGatewayDTO.from_api_gateway(requester_user)

    def __call__(self, request: IRequest) -> IResponse:
        try:
            requester = self._get_requester(request.data)

            limit_raw = request.data.get("limit")
            limit = self._parse_int(limit_raw, "limit") if limit_raw is not None else 20

            if limit < 1 or limit > 100:
                raise EntityError("limit")

            is_active = self._parse_bool(request.data.get("isActive", True), "isActive")

            system = request.data.get("system")
            if system is None:
                raise MissingParameters("system")
            if not isinstance(system, str):
                raise EntityError("system")

            name_filter = request.data.get("name")
            if name_filter is not None and not isinstance(name_filter, str):
                raise EntityError("name")

            last_evaluated_key = self._parse_last_key(
                request.data.get("last_evaluated_key")
            )

            templates, next_key = self.usecase(
                requester=requester,
                system=system,
                limit=limit,
                last_evaluated_key=last_evaluated_key,
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
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        except Exception as err:
            return InternalServerError(body=err.args[0] if err.args else str(err))
