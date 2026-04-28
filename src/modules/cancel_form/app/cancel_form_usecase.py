from typing import Optional
import uuid

from src.shared.domain.entities.file_upload import FileUpload, FileUploadRequest
from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms, utc_year
from src.shared.helpers.functions.s3_url import build_s3_url


class CancelFormUsecase:
    def __init__(self, form_repo: IFormRepository, file_repo: IFileRepository):
        self.form_repo = form_repo
        self.file_repo = file_repo

    def __call__(
        self,
        requester_id: str,
        form_id: str,
        selected_option: str,
        justification_text: Optional[str] = None,
        justification_image: Optional[FileUploadRequest] = None,
        cancelled_at: Optional[int] = None,
    ) -> Optional[FileUpload]:
        form = self.form_repo.get_form_by_id(user_id=requester_id, form_id=form_id)

        if form is None:
            raise NoItemsFound("Formulário não encontrado")

        form.ensure_assigned_to(requester_id, "Usuário não pode cancelar um formulário não direcionado a ele")

        expected_status = form.status
        file_upload: Optional[FileUpload] = None
        if justification_image:
            mimetype = justification_image.mimetype
            filename = justification_image.filename
            file_path = f'{utc_year()}/{form.system}/{form_id}/justification/{str(uuid.uuid4())}.{mimetype.split("/")[-1]}'
            presigned_url = self.file_repo.generate_presigned_url(
                file_path=file_path,
                mimetype=mimetype,
            )
            file_url = build_s3_url(file_path)
            justification_image = file_url
            file_upload = FileUpload(
                filename=filename,
                mimetype=mimetype,
                pre_signed_url=presigned_url,
                file_path=file_path,
                file_url=file_url,
            )

        updated_at = now_timestamp_ms()

        form.cancel(
            selected_option=selected_option,
            justification_text=justification_text,
            justification_image=justification_image,
            cancelled_at=cancelled_at if cancelled_at is not None else updated_at,
            updated_at=updated_at,
        )

        self.form_repo.update_form(
            user_id=requester_id,
            form_id=form_id,
            status=form.status,
            justification=form.justification,
            cancelled_at=form.cancelled_at,
            updated_at=form.updated_at,
            expected_status=expected_status,
        )
        return file_upload
