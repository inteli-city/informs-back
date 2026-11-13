from typing import List, Optional, Tuple

from pydantic import ValidationError

from .create_form_usecase import CreateFormUsecase
from .create_form_viewmodel import CreateFormViewmodel
from src.shared.domain.entities.creator_location import CreatorLocation
from src.shared.domain.entities.file_upload import FileUploadRequest
from src.shared.domain.entities.information_field import FileInformationField, InformationField
from src.shared.domain.enums.file_source_enum import FileSource
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.form_origin_enum import FormOrigin
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

        information_fields, information_fields_uploads = self._build_information_fields(payload)

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
            payload.external_id,
            FormOrigin(payload.origin) if payload.origin is not None else None,
            payload.service_type,
            payload.occurred_at,
            payload.scheduled_start_at,
            payload.scheduled_end_at,
            payload.attributes,
            CreatorLocation(**payload.creator_location.model_dump()) if payload.creator_location else None,
            payload.groups,
        )

    @classmethod
    def _build_information_fields(
        cls, payload: CreateFormControllerRequestSchema
    ) -> Tuple[Optional[List[InformationField]], Optional[List[Optional[FileUploadRequest]]]]:
        """Entidades dos campos informativos e, na mesma posição, o arquivo a
        enviar (só para FILE por upload; o resto fica `None`)."""
        if payload.information_fields is None:
            return None, None
        information_fields: List[InformationField] = []
        uploads: List[Optional[FileUploadRequest]] = []
        for information_field in (field.model_dump() for field in payload.information_fields):
            field, upload = cls._information_field(information_field)
            information_fields.append(field)
            uploads.append(upload)
        return information_fields, uploads

    @classmethod
    def _information_field(cls, information_field: dict) -> Tuple[InformationField, Optional[FileUploadRequest]]:
        if information_field.get("information_field_type") != "FILE_INFORMATION_FIELD":
            return InformationFieldDTO.from_request(information_field).to_entity(), None
        if information_field.get("source") == FileSource.URL.value:
            return cls._hosted_file(information_field), None
        return cls._uploaded_file(information_field)

    @staticmethod
    def _uploaded_file(information_field: dict) -> Tuple[FileInformationField, FileUploadRequest]:
        """Arquivo por upload: o caminho no S3 só existe depois, no usecase."""
        upload = FileUploadRequest(filename=information_field.get("filename"), mimetype=information_field.get("mimetype"))
        file_type_raw = information_field.get("file_type")
        file_type = FileType(file_type_raw) if file_type_raw is not None else None
        return FileInformationField(file_path="", file_type=file_type, key=information_field.get("key")), upload

    @staticmethod
    def _hosted_file(information_field: dict) -> FileInformationField:
        """Arquivo já hospedado por quem cria (ADR-0026): guarda o endereço, sem
        upload. A categoria sai do mimetype; o `file_type` do corpo, se vier,
        não pode contradizê-lo."""
        mimetype = information_field.get("mimetype")
        declared = FileType.IMAGE if mimetype.lower().startswith("image/") else FileType.DOCUMENT
        file_type_raw = information_field.get("file_type")
        if file_type_raw is not None and FileType(file_type_raw) != declared:
            raise EntityError("file_type")
        return FileInformationField(
            file_path=information_field.get("url"),
            file_type=declared,
            key=information_field.get("key"),
            source=FileSource.URL,
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
                external_id,
                origin,
                service_type,
                occurred_at,
                scheduled_start_at,
                scheduled_end_at,
                attributes,
                creator_location,
                groups,
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
                external_id=external_id,
                origin=origin,
                service_type=service_type,
                occurred_at=occurred_at,
                scheduled_start_at=scheduled_start_at,
                scheduled_end_at=scheduled_end_at,
                attributes=attributes,
                creator_location=creator_location,
                groups=groups,
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
