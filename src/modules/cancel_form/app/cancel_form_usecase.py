from typing import Optional
import uuid
from datetime import datetime, timezone

from src.shared.domain.entities.form import Form
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.image_repository_interface import IImageRepository
from src.shared.environments import Environments
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
        justification_image: Optional[str] = None,
        cancelled_at: Optional[int] = None,
    ) -> Form:
        
        form = self.form_repo.get_form_by_id(user_id=requester_id, form_id=form_id)

        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        
        if requester_id != form.user_id:
            raise ForbiddenAction("Usuário não pode cancelar um formulário não direcionado a ele")
        
        if justification_image:
            image_path = f'{datetime.now().year}/{form_id}/justification/{str(uuid.uuid4())}.png'
            self.image_repo.put_image(base_64_image=justification_image, image_path=image_path)
            justification_image = f'https://{Environments.get_envs().bucket_name}.s3.sa-east-1.amazonaws.com/{image_path}'

        updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)

        form.cancel(
            selected_option=selected_option,
            justification_text=justification_text,
            justification_image=justification_image,
            cancelled_at=cancelled_at if cancelled_at is not None else updated_at,
            updated_at=updated_at
        )

        return self.form_repo.cancel_form(
            user_id=requester_id,
            form_id=form_id,
            justification=form.justification,
            cancelled_at=form.cancelled_at,
            updated_at=form.updated_at
        )
