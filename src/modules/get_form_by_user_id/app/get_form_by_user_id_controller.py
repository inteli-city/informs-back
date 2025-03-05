from .get_form_by_user_id_usecase import GetFormByUserIdUsecase
from .get_form_by_user_id_viewmodel import GetFormByUserIdViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK, BadRequest, Forbidden, InternalServerError, NotFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO

class GetFormByUserIdController:
    def __init__(self, usecase: GetFormByUserIdUsecase):
        self.GetFormByUserIdUsecase = usecase

    def __call__(self, request: IRequest) -> IResponse:
        try:
            if request.data.get('requester_user') is None:
                raise MissingParameters('requester_user')

            requester_user = UserGatewayDTO.from_api_gateway(request.data.get('requester_user'))

            forms = self.GetFormByUserIdUsecase(requester_user_id=requester_user.user_id)
        
            viewmodel = GetFormByUserIdViewmodel(form_list=forms)
            
            return OK(viewmodel.to_dict())
        
        except NoItemsFound as err:
            return NotFound(body=err.message)

        except MissingParameters as err:
            return BadRequest(body=err.message)

        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        
        except Exception as err:
            return InternalServerError(body=err.args[0])