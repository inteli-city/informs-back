from typing import Optional
import uuid
from datetime import datetime

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.image_repository_interface import IImageRepository
from src.shared.environments import Environments
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


class CancelFormUsecase:
    def __init__(self, form_repo: IFormRepository, image_repo: IImageRepository):
        self.form_repo = form_repo
        self.image_repo = image_repo

    def __call__(self, requester_id: str, form_id: str, selected_option: str, justification_text: Optional[str] = None, justification_image: Optional[str] = None) -> Form:
        
        form = self.form_repo.get_form_by_id(user_id=requester_id, form_id=form_id)

        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        
        if requester_id != form.user_id:
            raise ForbiddenAction("Usuário não pode cancelar um formulário não direcionado a ele")
        
        if form.status == FORM_STATUS.CANCELED or form.status == FORM_STATUS.CONCLUDED:
            raise ForbiddenAction("Formulário já finalizado")
        
        for item in form.justification.options:
            if item.option == selected_option:
                if item.required_text and not justification_text:
                    raise EntityError("Justificativa de texto obrigatória")
                if item.required_image and not justification_image:
                    raise EntityError("Justificativa de imagem obrigatória")
            else:
                raise EntityError("Opção de justificativa inválida")
        
        if justification_image:
            image_path = f'{datetime.now().year}/{form_id}/justification/{str(uuid.uuid4())}.png'
            self.image_repo.put_image(base_64_image=justification_image, image_path=image_path)
            justification_image = f'https://{Environments.get_envs().bucket_name}.s3.sa-east-1.amazonaws.com/{image_path}'
            
        justification = Justification(
            options=form.justification.options,
            selected_option=selected_option,
            justification_text=justification_text,
            justification_image=justification_image
        )
        
        return self.form_repo.cancel_form(user_id=requester_id, form_id=form_id, justification=justification)
