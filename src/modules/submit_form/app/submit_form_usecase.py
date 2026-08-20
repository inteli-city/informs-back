from typing import Dict, List, Tuple
import uuid

from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.file_upload import FileUpload, FileUploadRequest
from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms, utc_year
from src.shared.helpers.functions.s3_url import build_s3_url


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
        form = self._get_form_or_raise(user_id=user_id, form_id=form_id)
        self._validate_form_can_be_submitted(form=form, user_id=user_id)
        file_uploads = form.apply_field_values(fields)
        files = self._upload_file_fields(form=form, form_id=form_id, file_uploads=file_uploads)
        self._complete_and_persist(form=form, user_id=user_id, form_id=form_id, completed_at=completed_at)
        return files

    def _get_form_or_raise(self, user_id: str, form_id: str) -> Form:
        form = self.form_repo.get_form_by_id(user_id=user_id, form_id=form_id)
        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        return form

    @staticmethod
    def _validate_form_can_be_submitted(form: Form, user_id: str) -> None:
        form.ensure_assigned_to(user_id, "Usuário não pode concluir um formulário não direcionado a ele")
        form.ensure_in_progress()

    def _upload_file_fields(
        self,
        form: Form,
        form_id: str,
        file_uploads: Dict[Tuple[int, int, str], List[FileUploadRequest]],
    ) -> list[FileUpload]:
        files: list[FileUpload] = []
        for section in form.sections:
            for field in section.fields:
                if self._should_upload_file_field(field):
                    files.extend(self._upload_file_field(form, form_id, section.section_id, section.section_instance, field, file_uploads))
        return files

    @classmethod
    def _should_upload_file_field(cls, field) -> bool:
        return isinstance(field, FileField) and cls._needs_upload(field.value)

    @staticmethod
    def _needs_upload(value) -> bool:
        if isinstance(value, dict):
            return True
        return isinstance(value, list) and bool(value) and isinstance(value[0], dict)

    def _upload_file_field(
        self,
        form: Form,
        form_id: str,
        section_id: int,
        section_instance: int,
        field: FileField,
        file_uploads: Dict[Tuple[int, int, str], List[FileUploadRequest]],
    ) -> list[FileUpload]:
        uploads = file_uploads.get((section_id, section_instance, field.key))
        if not uploads:
            raise EntityError("Uploads de arquivo não encontrados para o campo")

        files = []
        file_urls = []
        file_integrity = []
        for idx, upload in enumerate(uploads):
            file_upload = self._build_file_upload(form, form_id, section_id, section_instance, field.key, idx, upload)
            files.append(file_upload)
            file_urls.append(file_upload.file_url)
            file_integrity.append({
                "mimetype": file_upload.mimetype,
                "size_bytes": file_upload.size_bytes,
                "checksum_sha256": file_upload.checksum_sha256,
            })

        form.set_file_field_urls(section_id, field.key, file_urls, section_instance, file_integrity)
        return files

    def _build_file_upload(
        self,
        form: Form,
        form_id: str,
        section_id: int,
        section_instance: int,
        field_key: str,
        file_index: int,
        upload: FileUploadRequest,
    ) -> FileUpload:
        mimetype = upload.mimetype
        file_path = f'{utc_year()}/{form.system}/{form_id}/sections/{section_id}/{section_instance}/{str(uuid.uuid4())}.{mimetype.split("/")[-1]}'
        presigned_url = self.file_repo.generate_presigned_url(
            file_path=file_path,
            mimetype=mimetype,
            checksum_sha256=upload.checksum_sha256,
        )
        file_url = build_s3_url(file_path)

        return FileUpload(
            filename=upload.filename,
            mimetype=mimetype,
            pre_signed_url=presigned_url,
            file_path=file_path,
            file_url=file_url,
            section_id=section_id,
            section_instance=section_instance,
            field_key=field_key,
            file_index=file_index,
            size_bytes=upload.size_bytes,
            checksum_sha256=upload.checksum_sha256,
        )

    def _complete_and_persist(self, form: Form, user_id: str, form_id: str, completed_at: int) -> None:
        updated_at = now_timestamp_ms()
        form.complete(completed_at=completed_at, updated_at=updated_at)

        self.form_repo.update_form(
            user_id=user_id,
            form_id=form_id,
            status=form.status,
            sections=form.sections,
            completed_at=form.completed_at,
            updated_at=form.updated_at,
            expected_status=FormStatus.IN_PROGRESS,
        )
