from .complete_form_usecase import CompleteFormUsecase
from .complete_form_viewmodel import CompleteFormViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK, BadRequest, Forbidden, InternalServerError, NotFound
from src.shared.infra.dtos.section_dto import SectionDTO
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class CompleteFormController:
    def __init__(self, usecase: CompleteFormUsecase):
        self.CompleteFormUsecase = usecase
    
    def __call__(self, request: IRequest) -> IResponse:
        try:
            if request.data.get('requester_user') is None:
                raise MissingParameters('requester_user')
            
            requester_user = UserGatewayDTO.from_api_gateway(request.data.get('requester_user'))

            if request.data.get('form_id') is None:
                raise MissingParameters('form_id')
            
            sections = request.data.get('sections')
            if sections is None:
                raise MissingParameters('sections')
            if type(sections) is not list:
                raise WrongTypeParameter(fieldName='sections', fieldTypeExpected='list', fieldTypeReceived=type(request.data.get('sections')))
            sections= [SectionDTO.from_request(section).to_entity() for section in sections]

            if len(sections) == 0:
                raise MissingParameters('sections')
                        
            vinculation_form_id = request.data.get('vinculation_form_id')
            if vinculation_form_id is not None:
                if type(vinculation_form_id) is not str:
                    raise WrongTypeParameter(fieldName='vinculation_form_id', fieldTypeExpected='str', fieldTypeReceived=type(vinculation_form_id))
                
            form = self.CompleteFormUsecase(
                user_id=requester_user.user_id,
                form_id=request.data.get('form_id'),
                sections=sections,
                vinculation_form_id=request.data.get('vinculation_form_id')
            )

            viewmodel = CompleteFormViewmodel(form=form)
            
            return OK(viewmodel.to_dict())

        except NoItemsFound as err:
            return NotFound(body=err.message)

        except MissingParameters as err:
            return BadRequest(body=err.message)
        
        except WrongTypeParameter as err:
            return BadRequest(body= err.message)

        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        
        except Exception as err:
            return InternalServerError(body=err.args[0])