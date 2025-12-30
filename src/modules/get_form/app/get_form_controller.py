from .get_form_usecase import GetFormUsecase
from .get_form_viewmodel import GetFormViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, InternalServerError, NotFound, OK
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetFormController:
    def __init__(self, usecase: GetFormUsecase):
        self.usecase = usecase

    def _validate_requester_user(self, data: dict) -> UserGatewayDTO:
        requester_user = data.get("requester_user")
        if requester_user is None:
            raise MissingParameters("requester_user")

        return UserGatewayDTO.from_api_gateway(requester_user)

    def _validate_endpoint_parameters(self, data: dict) -> str:
        form_id = data.get("form_id")
        if form_id is None:
            raise MissingParameters("form_id")
        if not isinstance(form_id, str):
            raise WrongTypeParameter("form_id", "str", type(form_id))
        return form_id

    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            requester_user = self._validate_requester_user(data)
            form_id = self._validate_endpoint_parameters(data)

            form = self.usecase(
                requester_user_id=requester_user.user_id,
                form_id=form_id
            )

            viewmodel = GetFormViewmodel(form)
            return OK(viewmodel.to_dict())

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
