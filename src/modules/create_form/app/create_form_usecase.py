from copy import deepcopy
from typing import List, Optional
import uuid

from src.shared.domain.entities.file_upload import FileUpload, FileUploadRequest
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import FileInformationField, InformationField
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms, utc_year
from src.shared.helpers.functions.s3_url import build_s3_url


class CreateFormUsecase:
    def __init__(
        self,
        form_repo: IFormRepository,
        file_repo: IFileRepository,
        template_repo: Optional[ITemplateRepository] = None,
    ):
        self.form_repo = form_repo
        self.file_repo = file_repo
        self.template_repo = template_repo

    def __call__(
        self,
        form_title: str,
        created_by: str,
        user_id: str,
        system: str,
        street: str,
        city: str,
        latitude: float,
        longitude: float,
        priority: Priority,
        sections: List[Section],
        justification: Justification,
        template: Optional[str] = None,
        number: Optional[int] = None,
        observation: Optional[str] = None,
        expiration_date: Optional[int] = None,
        information_fields: Optional[List[InformationField]] = None,
        information_fields_uploads: Optional[List[Optional[FileUploadRequest]]] = None,
        requester_systems: Optional[List[str]] = None,
    ) -> tuple[Form, list[FileUpload]]:
        if requester_systems is not None and system not in requester_systems:
            raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")

        form_id = str(uuid.uuid4())
        now_timestamp = now_timestamp_ms()
        files: list[FileUpload] = []
        resolved_sections = sections

        if template is not None:
            if self.template_repo is None:
                raise EntityError("template")
            resolved_template = self.template_repo.get_template(template)
            if resolved_template is None:
                raise NoItemsFound("Template não encontrado")
            if resolved_template.system != system:
                raise ForbiddenAction("Template não pertence ao sistema informado")
            if not resolved_template.is_active:
                raise ForbiddenAction("Template não está ativo")
            resolved_sections = deepcopy(resolved_template.sections)

        if information_fields:
            uploads = information_fields_uploads or []
            for idx, information_field in enumerate(information_fields):
                if isinstance(information_field, FileInformationField):
                    if idx >= len(uploads) or uploads[idx] is None:
                        raise EntityError("mimetype")
                    upload = uploads[idx]
                    if not isinstance(upload, FileUploadRequest):
                        raise EntityError("mimetype")
                    mimetype = upload.mimetype
                    filename = upload.filename
                    file_path = f'{utc_year()}/{system}/{form_id}/information_field/{str(uuid.uuid4())}.{mimetype.split("/")[-1]}'
                    presigned_url = self.file_repo.generate_presigned_url(
                        file_path=file_path,
                        mimetype=mimetype,
                    )
                    file_url = build_s3_url(file_path)
                    information_field.file_path = file_url
                    if information_field.file_type is None:
                        if mimetype.lower().startswith("image/"):
                            information_field.file_type = FileType.IMAGE
                        else:
                            information_field.file_type = FileType.DOCUMENT
                    files.append(
                        FileUpload(
                            filename=filename,
                            mimetype=mimetype,
                            pre_signed_url=presigned_url,
                            file_path=file_path,
                            file_url=file_url,
                            section_id=None,
                            field_key=None,
                            file_index=None,
                        )
                    )

        form = Form(
            form_title=form_title,
            id=form_id,
            created_by=created_by,
            user_id=user_id,
            template=template,
            system=system,
            street=street,
            city=city,
            number=number,
            latitude=latitude,
            longitude=longitude,
            priority=priority,
            status=FormStatus.PENDING,
            created_at=now_timestamp,
            updated_at=now_timestamp,
            sections=resolved_sections,
            observation=observation,
            expiration_date=expiration_date,
            justification=justification,
            information_fields=information_fields,
        )

        created_form = self.form_repo.create_form(form)
        return created_form, files
