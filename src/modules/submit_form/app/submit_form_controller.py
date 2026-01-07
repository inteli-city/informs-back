from .submit_form_usecase import SubmitFormUsecase
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
            raise WrongTypeParameter(fieldName="form_id", fieldTypeExpected="str", fieldTypeReceived=type(form_id))

        completed_at_raw = data.get("completed_at")
        if completed_at_raw is None:
            raise MissingParameters("completed_at")

        if isinstance(completed_at_raw, bool) or not isinstance(completed_at_raw, int):
            raise WrongTypeParameter(fieldName="completed_at", fieldTypeExpected="int", fieldTypeReceived=type(completed_at_raw))

        completed_at = completed_at_raw

        sections_raw = data.get("sections")
        if sections_raw is None:
            raise MissingParameters("sections")
        if not isinstance(sections_raw, list):
            raise WrongTypeParameter(fieldName="sections", fieldTypeExpected="list", fieldTypeReceived=type(sections_raw))

        if len(sections_raw) == 0:
            raise MissingParameters("sections")

        sections = [SectionDTO.from_request(section).to_entity() for section in sections_raw]
        file_content_types = {}
        for section in sections_raw:
            section_id = section.get("section_id")
            for field in section.get("fields", []):
                if field.get("field_type") == "FILE_FIELD" and field.get("value") is not None:
                    content_type = field.get("content_type")
                    if content_type is None:
                        raise MissingParameters("content_type")
                    if not isinstance(content_type, str):
                        raise WrongTypeParameter(fieldName="content_type", fieldTypeExpected="str", fieldTypeReceived=type(content_type))
                    field_key = field.get("key")
                    file_content_types[(section_id, field_key)] = content_type

        return form_id, completed_at, sections, file_content_types
    
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            requester_user = self._validate_requester_user(data)
            form_id, completed_at, sections, file_content_types = self._validate_endpoint_parameters(data)
                
            self.submit_form_usecase(
                user_id=requester_user.user_id,
                form_id=form_id,
                sections=sections,
                completed_at=completed_at,
                file_content_types=file_content_types,
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
