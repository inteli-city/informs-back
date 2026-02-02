from typing import Optional
import uuid
from datetime import datetime, timezone

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.file_upload import FileUpload
from src.shared.domain.entities.file_upload import FileUploadRequest
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.helpers.functions.s3_url import build_s3_url
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


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
        
        if requester_id != form.user_id:
            raise ForbiddenAction("Usuário não pode cancelar um formulário não direcionado a ele")
        
        if form.status in [FORM_STATUS.CANCELLED, FORM_STATUS.COMPLETED]:
            raise ForbiddenAction("Formulário já está finalizado e não pode ser cancelado")

        file_upload: Optional[FileUpload] = None
        if justification_image:
            mimetype = justification_image.mimetype
            filename = justification_image.filename
            file_path = f'{datetime.now().year}/{form_id}/justification/{str(uuid.uuid4())}.{mimetype.split("/")[-1]}'
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
            

        updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)

        form.cancel(
            selected_option=selected_option,
            justification_text=justification_text,
            justification_image=justification_image,
            cancelled_at=cancelled_at if cancelled_at is not None else updated_at,
            updated_at=updated_at
        )

        self.form_repo.update_form(
            user_id=requester_id,
            form_id=form_id,
            status=form.status,
            justification=form.justification,
            cancelled_at=form.cancelled_at,
            updated_at=form.updated_at
        )
        return file_upload
