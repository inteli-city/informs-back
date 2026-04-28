from pydantic import ValidationError

from .get_all_forms_usecase import GetAllFormsUsecase
from .get_all_forms_viewmodel import GetAllFormsViewmodel
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.contracts.runtime_requests import GetAllFormsControllerRequestSchema
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, InvalidPaginationToken, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, NotFound, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAllFormsController:
    def __init__(self, usecase: GetAllFormsUsecase):
        self.usecase = usecase

    def _validate_status(self, status_raw):
        if status_raw is None:
            return None

        status_values = status_raw if isinstance(status_raw, list) else [status_raw]
        parsed_statuses = []
        for status_item in status_values:
            if not isinstance(status_item, str):
                raise WrongTypeParameter("status", "str", type(status_item))
            status_str = status_item.upper()
            if status_str not in FORM_STATUS.__members__:
                raise EntityError(f"Status '{status_str}' inválido. Valores aceitos: {list(FORM_STATUS.__members__.keys())}")
            parsed_statuses.append(FORM_STATUS[status_str])
        return parsed_statuses[0] if len(parsed_statuses) == 1 else parsed_statuses

    def _validate_system(self, system_raw):
        if system_raw is None:
            return None
        if isinstance(system_raw, list):
            if not all(isinstance(item, str) for item in system_raw):
                raise WrongTypeParameter("system", "list[str]", type(system_raw))
            return system_raw
        if isinstance(system_raw, str):
            return [system_raw]
        raise WrongTypeParameter("system", "list[str]", type(system_raw))

    def _validate_endpoint_parameters(self, payload: GetAllFormsControllerRequestSchema):
        limit = payload.limit
        if limit is not None and (limit < 1 or limit > 10000):
            raise EntityError(f"Parâmetro 'limit' deve ser um número entre 1 e 10000, recebido: {limit}")

        status = self._validate_status(payload.status)
        system = self._validate_system(payload.system)

        return (
            limit,
            status,
            system,
            payload.search,
            payload.created_at_start,
            payload.created_at_end,
            payload.exclusive_start_key,
        )

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = GetAllFormsControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            (
                limit,
                status,
                system,
                search,
                created_at_start,
                created_at_end,
                exclusive_start_key,
            ) = self._validate_endpoint_parameters(payload)

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

        except ValidationError as err:
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
