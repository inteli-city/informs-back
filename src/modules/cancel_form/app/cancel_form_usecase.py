from typing import Optional
import uuid
from datetime import datetime, timezone

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.image_upload import ImageUpload
from src.shared.domain.entities.image_upload import ImageUploadRequest
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.image_repository_interface import IImageRepository
from src.shared.helpers.functions.s3_url import build_s3_url
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


class CancelFormUsecase:
    def __init__(self, form_repo: IFormRepository, image_repo: IImageRepository):
        self.form_repo = form_repo
        self.image_repo = image_repo

    def __call__(
        self,
        requester_id: str,
        form_id: str,
        selected_option: str,
        justification_text: Optional[str] = None,
        justification_image: Optional[ImageUploadRequest] = None,
        cancelled_at: Optional[int] = None,
    ) -> Optional[ImageUpload]:
        
        form = self.form_repo.get_form_by_id(user_id=requester_id, form_id=form_id)

        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        
        if requester_id != form.user_id:
            raise ForbiddenAction("Usuário não pode cancelar um formulário não direcionado a ele")
        
        if form.status in [FORM_STATUS.CANCELLED, FORM_STATUS.COMPLETED]:
            raise ForbiddenAction("Formulário já está finalizado e não pode ser cancelado")

        image_upload: Optional[ImageUpload] = None
        if justification_image:
            mimetype = justification_image.mimetype
            filename = justification_image.filename
            image_path = f'{datetime.now().year}/{form_id}/justification/{str(uuid.uuid4())}.{mimetype.split("/")[-1]}'
            presigned_url = self.image_repo.generate_presigned_url(
                image_path=image_path,
                mimetype=mimetype,
            )
            image_url = build_s3_url(image_path)
            justification_image = image_url
            image_upload = ImageUpload(
                filename=filename,
                mimetype=mimetype,
                pre_signed_url=presigned_url,
                image_path=image_path,
                image_url=image_url,
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
        return image_upload
