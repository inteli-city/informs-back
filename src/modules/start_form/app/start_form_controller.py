from pydantic import ValidationError

from .start_form_usecase import StartFormUsecase
from src.shared.helpers.contracts.runtime_requests import StartFormControllerRequestSchema
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, InternalServerError, NoContent, NotFound
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class StartFormController:
    def __init__(self, usecase: StartFormUsecase):
        self.usecase = usecase

    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            if data.get("requester_user") is None:
                return BadRequest(body="Parâmetro ausente: requester_user")
            payload = StartFormControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            self.usecase(
                requester_user_id=requester_user.user_id,
                form_id=payload.form_id,
                in_progress_at=payload.in_progress_at
            )

            return NoContent()

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
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        except Exception as err:
            return InternalServerError(body=err.args[0])
