from .start_form_usecase import StartFormUsecase
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, InternalServerError, NoContent, NotFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class StartFormController:
    def __init__(self, usecase: StartFormUsecase):
        self.usecase = usecase

    def _validate_requester_user(self, data: dict) -> UserGatewayDTO:
        requester_user = data.get("requester_user")
        if requester_user is None:
            raise MissingParameters("requester_user")
        return UserGatewayDTO.from_api_gateway(requester_user)

    def _validate_endpoint_parameters(self, data: dict) -> tuple:
        form_id = data.get("form_id")
        if form_id is None:
            raise MissingParameters("form_id")
        if not isinstance(form_id, str):
            raise WrongTypeParameter("form_id", "str", type(form_id))

        in_progress_at_raw = data.get("in_progress_at")
        if in_progress_at_raw is None:
            raise MissingParameters("in_progress_at")

        if isinstance(in_progress_at_raw, bool) or not isinstance(in_progress_at_raw, int):
            raise WrongTypeParameter("in_progress_at", "int", type(in_progress_at_raw))

        in_progress_at = in_progress_at_raw

        return form_id, in_progress_at

    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            requester_user = self._validate_requester_user(data)
            form_id, in_progress_at = self._validate_endpoint_parameters(data)

            self.usecase(
                requester_user_id=requester_user.user_id,
                form_id=form_id,
                in_progress_at=in_progress_at
            )

            return NoContent()

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
