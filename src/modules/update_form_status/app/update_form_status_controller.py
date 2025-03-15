from .update_form_status_usecase import UpdateFormStatusUsecase
from .update_form_status_viewmodel import UpdateFormStatusViewmodel
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK, BadRequest, Conflict, Forbidden, InternalServerError, NotFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class UpdateFormStatusController:
    def __init__(self, usecase: UpdateFormStatusUsecase):
        self.UpdateFormStatusUsecase = usecase

    def __call__(self, request: IRequest) -> IResponse:
        try:
            if request.data.get('requester_user') is None:
                raise MissingParameters('requester_user')
            
            requester_user = UserGatewayDTO.from_api_gateway(request.data.get('requester_user'))

            if request.data.get('form_id') is None:
                raise MissingParameters('form_id')

            if request.data.get('status') is None:
                raise MissingParameters('status')
            
            if request.data.get('status') not in ['NOT_STARTED', 'IN_PROGRESS']:
                raise EntityError('status')
            
            form = self.UpdateFormStatusUsecase(
                user=requester_user,
                form_id=request.data.get('form_id'),
                status=FORM_STATUS[request.data.get('status')]
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
        
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")

        except Exception as err:
            return InternalServerError(body=err.args[0])