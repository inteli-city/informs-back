from pydantic import ValidationError

from .create_form_usecase import CreateFormUsecase
from .create_form_viewmodel import CreateFormViewmodel
from src.shared.domain.entities.file_upload import FileUploadRequest
from src.shared.domain.entities.information_field import FileInformationField
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.contracts.runtime_requests import CreateFormControllerRequestSchema
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import (
    BadRequest,
    Conflict,
    Created,
    Forbidden,
    NotFound,
)
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.information_field_dto import InformationFieldDTO
from src.shared.infra.dtos.justification_dto import JustificationDTO
from src.shared.infra.dtos.section_dto import SectionDTO
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class CreateFormController:
    def __init__(self, usecase: CreateFormUsecase):
        self.usecase = usecase

    def _build_usecase_payload(self, payload: CreateFormControllerRequestSchema) -> tuple:
        priority = Priority(str(payload.priority))

        sections_raw = [section.model_dump() for section in (payload.sections or [])]
        sections = [SectionDTO.from_request(section).to_entity() for section in sections_raw]

        normalized_justifications = [option.model_dump() for option in payload.justifications]
        justification_entity = JustificationDTO.from_request({"options": normalized_justifications}).to_entity()

        information_fields = None
        information_fields_uploads = None
        if payload.information_fields is not None:
            information_fields = []
            info_raw = [field.model_dump() for field in payload.information_fields]
            information_fields_uploads = [None] * len(info_raw)

            for idx, information_field in enumerate(info_raw):
                info_type = information_field.get("information_field_type")
                if info_type == "FILE_INFORMATION_FIELD":
                    mimetype = information_field.get("mimetype")
                    filename = information_field.get("filename")
                    information_fields_uploads[idx] = FileUploadRequest(filename=filename, mimetype=mimetype)

                    file_type_raw = information_field.get("file_type")
                    file_type = FileType(file_type_raw) if file_type_raw is not None else None
                    information_fields.append(FileInformationField(file_path="", file_type=file_type))
                else:
                    information_fields.append(InformationFieldDTO.from_request(information_field).to_entity())

        return (
            payload.form_title,
            payload.user_id,
            payload.system,
            payload.street,
            payload.city,
            payload.latitude,
            payload.longitude,
            priority,
            sections,
            justification_entity,
            payload.number,
            payload.observation,
            payload.expiration_date,
            payload.template,
            information_fields,
            information_fields_uploads,
        )

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = CreateFormControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))
            (
                form_title,
                user_id,
                system,
                street,
                city,
                latitude,
                longitude,
                priority,
                sections,
                justification_entity,
                number,
                observation,
                expiration_date,
                template,
                information_fields,
                information_fields_uploads,
            ) = self._build_usecase_payload(payload)

            form, files = self.usecase(
                form_title=form_title,
                created_by=requester_user.user_id,
                user_id=user_id,
                system=system,
                street=street,
                city=city,
                latitude=latitude,
                longitude=longitude,
                priority=priority,
                sections=sections,
                justification=justification_entity,
                number=number,
                observation=observation,
                expiration_date=expiration_date,
                template=template,
                information_fields=information_fields,
                information_fields_uploads=information_fields_uploads,
                requester_systems=requester_user.systems,
            )

            viewmodel = CreateFormViewmodel(form=form, files=files)
            return Created(viewmodel.to_dict())

        except ValidationError as err:
            if "sections is required when template is not a UUID" in str(err):
                return BadRequest(body="Parâmetro ausente: sections")
            return BadRequest(body=get_validation_error_message(err))
        except NoItemsFound as err:
            return NotFound(body=err.message)
        except DuplicatedItem as err:
            return Conflict(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        except WrongTypeParameter as err:
            return BadRequest(body=err.message)
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
