from pydantic import ValidationError

from .propagate_template_usecase import PropagateTemplateUsecase
from .propagate_template_viewmodel import PropagateTemplateViewmodel
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.contracts.runtime_requests import PropagateTemplateControllerRequestSchema
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, NotFound, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class PropagateTemplateController:
    def __init__(self, usecase: PropagateTemplateUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = PropagateTemplateControllerRequestSchema.model_validate(data)
            requester = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            result = self.usecase(
                template_id=payload.template_id,
                requester=requester,
                form_ids=payload.form_ids,
            )
            return OK(PropagateTemplateViewmodel(result).to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        except NoItemsFound as err:
            return NotFound(body=err.message)
        except ForbiddenAction as err:
            return Forbidden(body=err.message)
