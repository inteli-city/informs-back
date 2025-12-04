from typing import Optional

from .get_all_forms_usecase import GetAllFormsUsecase
from .get_all_forms_viewmodel import GetAllFormsViewmodel
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, InternalServerError, NotFound, OK
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAllFormsController:
    def __init__(self, usecase: GetAllFormsUsecase):
        self.usecase = usecase

    def _parse_int(self, value: Optional[str], field_name: str) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            raise EntityError(field_name)

    def __call__(self, request: IRequest) -> IResponse:
        try:
            if request.data.get('requester_user') is None:
                raise MissingParameters('requester_user')

            requester_user = UserGatewayDTO.from_api_gateway(request.data.get('requester_user'))

            page = self._parse_int(request.data.get('page', 1), 'page') or 1
            limit = self._parse_int(request.data.get('limit', 20), 'limit') or 20

            if page < 1:
                raise EntityError('page')
            if limit < 20 or limit > 100:
                raise EntityError('limit')

            status = None
            if request.data.get('status') is not None:
                status_str = str(request.data.get('status')).upper()
                if status_str not in FORM_STATUS.__members__:
                    raise EntityError('status')
                status = FORM_STATUS[status_str]

            system = request.data.get('system')
            search = request.data.get('search')
            created_at_start = self._parse_int(request.data.get('created_at_start'), 'created_at_start')
            created_at_end = self._parse_int(request.data.get('created_at_end'), 'created_at_end')

            forms = self.usecase(
                requester_user_id=requester_user.user_id,
                page=page,
                limit=limit,
                status=status,
                system=system,
                created_at_start=created_at_start,
                created_at_end=created_at_end,
                search=search
            )

            viewmodel = GetAllFormsViewmodel(forms=forms, page=page, limit=limit)
            return OK(viewmodel.to_dict())

        except NoItemsFound as err:
            return NotFound(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except ForbiddenAction as err:
            return BadRequest(body=err.message)
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        except Exception as err:
            return InternalServerError(body=err.args[0])
