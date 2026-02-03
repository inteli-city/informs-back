from typing import List
import uuid
from datetime import datetime
from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.file_upload import FileUpload
from src.shared.domain.entities.file_upload import FileUploadRequest
from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.infra.dtos.field_dto import FieldDTO
from src.shared.helpers.functions.s3_url import build_s3_url
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


class SubmitFormUsecase:

    def __init__(self, form_repo: IFormRepository, file_repo: IFileRepository):
        self.form_repo = form_repo
        self.file_repo = file_repo
    
    def __call__(
        self,
        user_id: str,
        form_id: str,
        fields: List[dict],
        completed_at: int,
    ) -> list[FileUpload]:
        form = self.form_repo.get_form_by_id(user_id=user_id, form_id=form_id)

        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        
        if user_id != form.user_id:
            raise ForbiddenAction("Usuário não pode concluir um formulário não direcionado a ele")
        
        if form.status is not FORM_STATUS.IN_PROGRESS:
            raise ForbiddenAction("Formulário não está em andamento")
        
        sections_by_id = {section.section_id: section for section in form.sections}
        seen = set()
        file_uploads = {}

        for item in fields:
            section_id = item.get("section_id")
            field_key = item.get("field_key")
            value = item.get("value")

            key = (section_id, field_key)
            if key in seen:
                raise EntityError("field_key")
            seen.add(key)

            section = sections_by_id.get(section_id)
            if section is None:
                raise EntityError("section_id")

            field_index = next((idx for idx, field in enumerate(section.fields) if field.key == field_key), None)
            if field_index is None:
                raise EntityError("field_key")

            existing_field = section.fields[field_index]
            field_dict = FieldDTO(existing_field).to_dynamo()

            if isinstance(existing_field, FileField) and value is not None:
                uploads_raw = value
                if isinstance(uploads_raw, dict):
                    uploads_raw = [uploads_raw]
                if not isinstance(uploads_raw, list) or not uploads_raw:
                    raise EntityError("mimetype")
                normalized_uploads = []
                for upload in uploads_raw:
                    if not isinstance(upload, dict):
                        raise EntityError("mimetype")
                    filename = upload.get("filename")
                    mimetype = upload.get("mimetype")
                    if filename is None or mimetype is None:
                        raise EntityError("mimetype")
                    if not isinstance(filename, str) or not isinstance(mimetype, str):
                        raise EntityError("mimetype")
                    normalized_uploads.append(FileUploadRequest(filename=filename, mimetype=mimetype))
                file_uploads[(section_id, field_key)] = normalized_uploads
                field_dict["value"] = uploads_raw
            else:
                field_dict["value"] = value

            updated_field = FieldDTO.from_dynamo(field_dict).to_entity()
            section.fields[field_index] = updated_field

        for section in form.sections:
            for field in section.fields:
                if field.required and field.value is None:
                    raise ForbiddenAction("Campo obrigatório não preenchido")
        
        files: list[FileUpload] = []
        def _needs_upload(value) -> bool:
            if isinstance(value, dict):
                return True
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return True
            return False

        for section in form.sections:
            for field in section.fields:
                if isinstance(field, FileField) and field.value is not None and _needs_upload(field.value):
                    uploads = file_uploads.get((section.section_id, field.key))
                    if not uploads:
                        raise EntityError("mimetype")
                    file_urls = []
                    for idx, upload in enumerate(uploads):
                        if not isinstance(upload, FileUploadRequest):
                            raise EntityError("mimetype")
                        mimetype = upload.mimetype
                        filename = upload.filename
                        file_path = f'{datetime.now().year}/{form_id}/sections/{section.section_id}/{str(uuid.uuid4())}.{mimetype.split("/")[-1]}'
                        presigned_url = self.file_repo.generate_presigned_url(
                            file_path=file_path,
                            mimetype=mimetype,
                        )
                        file_url = build_s3_url(file_path)
                        file_urls.append(file_url)
                        files.append(
                            FileUpload(
                                filename=filename,
                                mimetype=mimetype,
                                pre_signed_url=presigned_url,
                                file_path=file_path,
                                file_url=file_url,
                                section_id=section.section_id,
                                field_key=field.key,
                                file_index=idx,
                            )
                        )
                    field.value = file_urls[0] if len(file_urls) == 1 else file_urls
        
        updated_at = int(datetime.now().timestamp() * 1000)
        
        self.form_repo.update_form(
            user_id=user_id,
            form_id=form_id,
            status=FORM_STATUS.COMPLETED,
            sections=form.sections,
            completed_at=completed_at,
            updated_at=updated_at
        )
        return files
