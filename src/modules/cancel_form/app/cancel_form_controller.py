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
        self.CancelFormUsecase = usecase
    
    def __call__(self, request: IRequest) -> IResponse:
        try:
            if request.data.get('requester_user') is None:
                raise MissingParameters('requester_user')
            
            requester_user = UserGatewayDTO.from_api_gateway(request.data.get('requester_user'))

            if request.data.get('form_id') is None:
                raise MissingParameters('form_id')
            
            selected_option = request.data.get('selected_option') or request.data.get('option')
            if selected_option is None:
                raise MissingParameters('selected_option')
            if type(selected_option) is not str:
                raise WrongTypeParameter(fieldName='selected_option', fieldTypeExpected='str', fieldTypeReceived=type(request.data.get('selected_option')))
            
            justification_text = request.data.get('justification_text') or request.data.get('text')
            if justification_text is not None:
                if type(justification_text) is not str:
                    raise WrongTypeParameter(fieldName='justification_text', fieldTypeExpected='str', fieldTypeReceived=type(justification_text))
            
            justification_image = request.data.get('justification_image') or request.data.get('image')
            if justification_image is not None:
                if type(justification_image) is not str:
                    raise WrongTypeParameter(fieldName='justification_image', fieldTypeExpected='str', fieldTypeReceived=type(justification_image))

            if request.data.get('cancelled_at') is None:
                raise MissingParameters('cancelled_at')
            try:
                cancelled_at = int(request.data.get('cancelled_at'))
            except (TypeError, ValueError):
                raise WrongTypeParameter(fieldName='cancelled_at', fieldTypeExpected='int', fieldTypeReceived=type(request.data.get('cancelled_at')))
            
            form = self.CancelFormUsecase(
                requester_id=requester_user.user_id,
                form_id=request.data.get('form_id'),
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
