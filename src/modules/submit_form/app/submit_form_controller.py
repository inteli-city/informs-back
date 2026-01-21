from .submit_form_usecase import SubmitFormUsecase
from .submit_form_viewmodel import SubmitFormViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK, BadRequest, Forbidden, InternalServerError, NotFound
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
        file_uploads = {}
        for section in sections_raw:
            section_id = section.get("section_id")
            for field in section.get("fields", []):
                if field.get("field_type") == "FILE_FIELD" and field.get("value") is not None:
                    field_key = field.get("key")
                    uploads = field.get("value")
                    if isinstance(uploads, dict):
                        uploads = [uploads]
                    if not isinstance(uploads, list) or not uploads:
                        raise MissingParameters("value")
                    normalized = []
                    for upload in uploads:
                        if not isinstance(upload, dict):
                            raise WrongTypeParameter(fieldName="value", fieldTypeExpected="dict", fieldTypeReceived=type(upload))
                        filename = upload.get("filename")
                        if filename is None:
                            raise MissingParameters("filename")
                        if not isinstance(filename, str):
                            raise WrongTypeParameter(fieldName="filename", fieldTypeExpected="str", fieldTypeReceived=type(filename))
                        mimetype = upload.get("mimetype")
                        if mimetype is None:
                            raise MissingParameters("mimetype")
                        if not isinstance(mimetype, str):
                            raise WrongTypeParameter(fieldName="mimetype", fieldTypeExpected="str", fieldTypeReceived=type(mimetype))
                        normalized.append({"filename": filename, "mimetype": mimetype})
                    file_uploads[(section_id, field_key)] = normalized

        return form_id, completed_at, sections, file_uploads
    
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            requester_user = self._validate_requester_user(data)
            form_id, completed_at, sections, file_uploads = self._validate_endpoint_parameters(data)
                
            images = self.submit_form_usecase(
                user_id=requester_user.user_id,
                form_id=form_id,
                sections=sections,
                completed_at=completed_at,
                file_uploads=file_uploads,
            )

            viewmodel = SubmitFormViewmodel(images=images)
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
