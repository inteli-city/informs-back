from .cancel_form_usecase import CancelFormUsecase
from .cancel_form_viewmodel import CancelFormViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK, BadRequest, Conflict, Forbidden, InternalServerError, NotFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class CancelFormController:
    def __init__(self, usecase: CancelFormUsecase):
        self.usecase = usecase

    def _validate_requester_user(self, data: dict) -> UserGatewayDTO:
        requester_user_data = data.get("requester_user")
        if requester_user_data is None:
            raise MissingParameters("requester_user")

        return UserGatewayDTO.from_api_gateway(requester_user_data)
    
    def _validate_endpoint_parameters(self, data: dict) -> tuple:
        form_id = data.get("form_id")
        if form_id is None:
            raise MissingParameters("form_id")
        if not isinstance(form_id, str):
            raise WrongTypeParameter(fieldName="form_id", fieldTypeExpected="str", fieldTypeReceived=type(form_id))
        
        selected_option = data.get("selected_option") or data.get("option")
        if selected_option is None:
            raise MissingParameters("selected_option")
        if not isinstance(selected_option, str):
            raise WrongTypeParameter(fieldName="selected_option", fieldTypeExpected="str", fieldTypeReceived=type(selected_option))
        
        justification_text = data.get("justification_text") or data.get("text")
        if justification_text is not None and not isinstance(justification_text, str):
            raise WrongTypeParameter(fieldName="justification_text", fieldTypeExpected="str", fieldTypeReceived=type(justification_text))
        
        justification_image = data.get("justification_image") or data.get("image")
        if justification_image is not None and not isinstance(justification_image, str):
            raise WrongTypeParameter(fieldName="justification_image", fieldTypeExpected="str", fieldTypeReceived=type(justification_image))

        cancelled_at = data.get("cancelled_at")
        if cancelled_at is not None:
            if isinstance(cancelled_at, bool) or not isinstance(cancelled_at, int):
                raise WrongTypeParameter(fieldName="cancelled_at", fieldTypeExpected="int", fieldTypeReceived=type(cancelled_at))
        return (form_id, selected_option, justification_text, justification_image, cancelled_at)
    
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            requester_user = self._validate_requester_user(data)

            form_id, selected_option, justification_text, justification_image, cancelled_at = self._validate_endpoint_parameters(data)
            
            form = self.usecase(
                requester_id=requester_user.user_id,
                form_id=form_id,
                selected_option=selected_option,
                justification_text=justification_text,
                justification_image=justification_image,
                cancelled_at=cancelled_at
            )

            viewmodel = CancelFormViewmodel(form=form)
            
            return OK(viewmodel.to_dict())
        
        except NoItemsFound as err:
            return NotFound(body=err.message)

        except MissingParameters as err:
            return BadRequest(body= err.message)
        
        except WrongTypeParameter as err:
            return BadRequest(body=err.message)

        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        
        except Exception as err:
            return InternalServerError(body=err.args[0])
