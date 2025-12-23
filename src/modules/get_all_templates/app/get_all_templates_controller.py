from typing import Optional

from .get_all_templates_usecase import GetAllTemplatesUsecase
from .get_all_templates_viewmodel import GetAllTemplatesViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, InternalServerError, NotFound, OK
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

    def _get_requester(self, data: dict) -> UserGatewayDTO:
        requester_user = data.get("requester_user")
        if requester_user is None:
            raise MissingParameters("requester_user")
        return UserGatewayDTO.from_api_gateway(requester_user)

    def __call__(self, request: IRequest) -> IResponse:
        try:
            self._get_requester(request.data)

            page = self._parse_int(request.data.get("page", 1), "page")
            limit = self._parse_int(request.data.get("limit", 20), "limit")

            if page < 1:
                raise EntityError("page")
            if limit < 20 or limit > 100:
                raise EntityError("limit")

            is_active = self._parse_bool(request.data.get("isActive"), "isActive")

            system = request.data.get("system")
            if system is not None and not isinstance(system, str):
                raise EntityError("system")

            templates = self.usecase(
                page=page,
                limit=limit,
                is_active=is_active,
                system=system,
            )

            viewmodel = GetAllTemplatesViewmodel(templates=templates, page=page, limit=limit)
            return OK(viewmodel.to_dict())

        except NoItemsFound as err:
            return NotFound(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        except Exception as err:
            return InternalServerError(body=err.args[0] if err.args else str(err))
