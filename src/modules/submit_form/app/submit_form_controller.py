from .submit_form_usecase import SubmitFormUsecase
from .submit_form_viewmodel import SubmitFormViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import NoContent, BadRequest, Forbidden, InternalServerError, NotFound
from src.shared.infra.dtos.section_dto import SectionDTO
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class SubmitFormController:
    def __init__(self, usecase: SubmitFormUsecase):
        self.submit_form_usecase = usecase
    
    def __call__(self, request: IRequest) -> IResponse:
        try:
            if request.data.get('requester_user') is None:
                raise MissingParameters('requester_user')
            
            requester_user = UserGatewayDTO.from_api_gateway(request.data.get('requester_user'))

            if request.data.get('form_id') is None:
                raise MissingParameters('form_id')
            completed_at = request.data.get('completed_at')
            if completed_at is None:
                raise MissingParameters('completed_at')
            try:
                completed_at = int(completed_at)
            except (TypeError, ValueError):
                raise WrongTypeParameter(fieldName='completed_at', fieldTypeExpected='int', fieldTypeReceived=type(completed_at))

            sections = request.data.get('sections')
            if sections is None:
                raise MissingParameters('sections')
            if type(sections) is not list:
                raise WrongTypeParameter(fieldName='sections', fieldTypeExpected='list', fieldTypeReceived=type(request.data.get('sections')))
            sections= [SectionDTO.from_request(section).to_entity() for section in sections]

            if len(sections) == 0:
                raise MissingParameters('sections')
                
            form = self.submit_form_usecase(
                user_id=requester_user.user_id,
                form_id=request.data.get('form_id'),
                sections=sections,
                completed_at=completed_at
            )

            return NoContent()

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
