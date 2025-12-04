from .create_form_usecase import CreateFormUsecase
from .create_form_viewmodel import CreateFormViewmodel
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
                raise MissingParameters('user_id')
            
            if request.data.get('system') is None:
                raise MissingParameters('system')
            
            if request.data.get('street') is None:
                raise MissingParameters('street')
            
            if request.data.get('city') is None:
                raise MissingParameters('city')
            
            if request.data.get('latitude') is None:
                raise MissingParameters('latitude')
            
            if request.data.get('longitude') is None:
                raise MissingParameters('longitude')
            
            if request.data.get('priority') is None:
                raise MissingParameters('priority')
            
            if request.data.get('justifications') is None:
                raise MissingParameters('justifications')
            
            if request.data.get('sessions') is None:
                raise MissingParameters('sessions')

            priority_payload = request.data.get('priority')
            try:
                if isinstance(priority_payload, str) and priority_payload.upper() in PRIORITY.__members__:
                    priority = PRIORITY[priority_payload.upper()]
                else:
                    priority = PRIORITY(str(int(priority_payload)))
            except Exception:
                raise EntityError('priority')

            raw_justifications = request.data.get('justifications') or []
            normalized_justifications = [
                {
                    "option": option.get('option'),
                    "required_image": bool(option.get('required_image')) if option.get('required_image') is not None else False,
                    "required_text": bool(option.get('required_text')) if option.get('required_text') is not None else False
                }
                for option in raw_justifications
            ]

            justification_entity = JustificationDTO.from_request({"options": normalized_justifications}).to_entity()

            try:
                latitude = float(request.data.get('latitude'))
                longitude = float(request.data.get('longitude'))
            except (TypeError, ValueError):
                raise EntityError('latitude/longitude')

            expiration_date = request.data.get('expiration_date')
            if expiration_date is not None:
                try:
                    expiration_date = int(expiration_date)
                except (TypeError, ValueError):
                    raise EntityError('expiration_date')

            number = request.data.get('number')
            if number is not None:
                try:
                    number = int(number)
                except (TypeError, ValueError):
                    raise EntityError('number')

            form = self.CreateFormUsecase(
                form_title=request.data.get('form_title'),
                creator_user_id=requester_user.user_id,
                user_id=request.data.get('user_id'),
                system=request.data.get('system'),
                street=request.data.get('street'),
                city=request.data.get('city'),
                latitude=latitude,
                longitude=longitude,
                priority=priority,
                sections=[
                    SectionDTO.from_request(section).to_entity()
                    for section in request.data.get('sessions')
                ],
                justification=justification_entity,
                number=number,
                observation=request.data.get('observation'),
                expiration_date=expiration_date,
                information_fields=[
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
