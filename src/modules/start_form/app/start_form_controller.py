from .start_form_usecase import StartFormUsecase
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, InternalServerError, NoContent, NotFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class StartFormController:
    def __init__(self, usecase: StartFormUsecase):
        self.usecase = usecase

    def __call__(self, request: IRequest) -> IResponse:
        try:
            if request.data.get('requester_user') is None:
                raise MissingParameters('requester_user')

            requester_user = UserGatewayDTO.from_api_gateway(request.data.get('requester_user'))

            if request.data.get('form_id') is None:
                raise MissingParameters('form_id')

            if request.data.get('in_progress_at') is None:
                raise MissingParameters('in_progress_at')

            try:
                in_progress_at = int(request.data.get('in_progress_at'))
            except (TypeError, ValueError):
                raise EntityError('in_progress_at')

            self.usecase(
                requester_user_id=requester_user.user_id,
                form_id=request.data.get('form_id'),
                in_progress_at=in_progress_at
            )

            return NoContent()

        except NoItemsFound as err:
            return NotFound(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        except Exception as err:
            return InternalServerError(body=err.args[0])
