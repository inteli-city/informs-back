from .update_form_status_usecase import UpdateFormStatusUsecase
from .update_form_status_viewmodel import UpdateFormStatusViewmodel
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK, BadRequest, Conflict, Forbidden, InternalServerError, NotFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class UpdateFormStatusController:
    def __init__(self, usecase: UpdateFormStatusUsecase):
        self.UpdateFormStatusUsecase = usecase

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

        status_raw = data.get("status")
        if status_raw is None:
            raise MissingParameters("status")
        if not isinstance(status_raw, str):
            raise WrongTypeParameter("status", "str", type(status_raw))
        if status_raw not in ["PENDING", "IN_PROGRESS"]:
            raise EntityError("status")

        return form_id, FORM_STATUS[status_raw]

    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            requester_user = self._validate_requester_user(data)
            form_id, status = self._validate_endpoint_parameters(data)
            
            form = self.UpdateFormStatusUsecase(
                user=requester_user,
                form_id=form_id,
                status=status
            )
        
            viewmodel = UpdateFormStatusViewmodel(form=form)

            return OK(viewmodel.to_dict())

        except NoItemsFound as err:
            return NotFound(body=err.message)

        except MissingParameters as err:
            return BadRequest(body=err.message)
        
        except DuplicatedItem as err:
            return Conflict(body=err.message)

        except ForbiddenAction as err:
            return Forbidden(body= err.message)
        except WrongTypeParameter as err:
            return BadRequest(body=err.message)
        
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")

        except Exception as err:
            return InternalServerError(body=err.args[0])
