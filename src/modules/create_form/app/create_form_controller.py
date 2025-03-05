from .create_form_usecase import CreateFormUsecase
from .create_form_viewmodel import CreateFormViewmodel
from src.shared.domain.entities.information_field import TextInformationField
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, Created, Forbidden, InternalServerError, NotFound
from src.shared.infra.dtos.information_field_dto import InformationFieldDTO
from src.shared.infra.dtos.justification_dto import JustificationDTO
from src.shared.infra.dtos.section_dto import SectionDTO
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class CreateFormController:
    def __init__(self, usecase: CreateFormUsecase):
        self.CreateFormUsecase = usecase
    
    def __call__(self, request: IRequest) -> IResponse:
        try:
            if request.data.get('requester_user') is None:
                raise MissingParameters('requester_user')
            
            requester_user = UserGatewayDTO.from_api_gateway(request.data.get('requester_user'))

            if request.data.get('form_title') is None:
                raise MissingParameters('form_title')
            
            if request.data.get('user_id') is None:
                request.data['user_id'] = requester_user.user_id
            
            if request.data.get('can_vinculate') is None:
                raise MissingParameters('can_vinculate')
            
            if request.data.get('template') is None:
                raise MissingParameters('template')
            
            if request.data.get('area') is None:
                raise MissingParameters('area')
            
            if request.data.get('system') is None:
                raise MissingParameters('system')
            
            if request.data.get('street') is None:
                raise MissingParameters('street')
            
            if request.data.get('city') is None:
                raise MissingParameters('city')
            
            if request.data.get('number') is None:
                raise MissingParameters('number')
            
            if request.data.get('latitude') is None:
                raise MissingParameters('latitude')
            
            if request.data.get('longitude') is None:
                raise MissingParameters('longitude')
            
            if request.data.get('region') is None:
                raise MissingParameters('region')
            
            if request.data.get('priority') is None:
                raise MissingParameters('priority')
            
            if request.data.get('priority') not in [enum.value for enum in PRIORITY]:
                raise EntityError('priority')
            
            if request.data.get('expiration_date') is None:
                raise MissingParameters('expiration_date')
            
            if request.data.get('justification') is None:
                raise MissingParameters('justification')
            
            if request.data.get('sections') is None:
                raise MissingParameters('sections')
            
            form = self.CreateFormUsecase(
                form_title=request.data.get('form_title'),
                creator_user_id=requester_user.user_id,
                user_id=request.data.get('user_id'),
                vinculation_form_id=request.data.get('vinculation_form_id'),
                can_vinculate=request.data.get('can_vinculate'),
                template=request.data.get('template'),
                area=request.data.get('area'),
                system=request.data.get('system'),
                street=request.data.get('street'),
                city=request.data.get('city'),
                number=request.data.get('number'),
                latitude=request.data.get('latitude'),
                longitude=request.data.get('longitude'),
                region=request.data.get('region'),
                description=request.data.get('description'),
                priority=PRIORITY[request.data.get('priority')],
                expiration_date=request.data.get('expiration_date'),
                justification=JustificationDTO.from_request(request.data.get('justification')).to_entity(),
                comments=request.data.get('comments'),
                sections=[
                    SectionDTO.from_request(section).to_entity()
                    for section in request.data.get('sections')
                ],
                information_fields= [
                    InformationFieldDTO.from_request(information_field).to_entity()
                    for information_field in request.data.get('information_fields')
                ] if request.data.get('information_fields') is not None else None
            )

            viewmodel = CreateFormViewmodel(form=form)
            
            return Created(viewmodel.to_dict())
        
        except NoItemsFound as err:
            return NotFound(body=err.message)
        
        except DuplicatedItem as err:
            return Conflict(body=err.message)

        except MissingParameters as err:
            return BadRequest(body= err.message)

        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        
        except Exception as err:
            return InternalServerError(body=err.args[0])