from typing import List, Optional
import uuid
from datetime import datetime
from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.image_repository_interface import IImageRepository
from src.shared.environments import Environments
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


class SubmitFormUsecase:

    def __init__(self, form_repo: IFormRepository, image_repo: IImageRepository):
        self.form_repo = form_repo
        self.image_repo = image_repo
    
    def __call__(self, user_id: str, form_id: str, sections: List[Section], completed_at: int) -> Form:
        form = self.form_repo.get_form_by_id(user_id=user_id, form_id=form_id)

        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        
        if user_id != form.user_id:
            raise ForbiddenAction("Usuário não pode concluir um formulário não direcionado a ele")
        
        if form.status is not FORM_STATUS.IN_PROGRESS:
            raise ForbiddenAction("Formulário não está em andamento")
        
        for section in sections:
            for field in section.fields:
                if field.required and field.value is None:
                    raise ForbiddenAction("Campo obrigatório não preenchido")
        
        for section in sections:
            for field in section.fields:
                if isinstance(field, FileField):
                    image_path = f'{datetime.now().year}/{form_id}/sections/{section.section_id}/{str(uuid.uuid4())}.png'
                    self.image_repo.put_image(base_64_image=field.value, image_path=image_path)
                    field.value = f'https://{Environments.get_envs().bucket_name}.s3.sa-east-1.amazonaws.com/{image_path}'
        
        updated_at = int(datetime.now().timestamp() * 1000)
        
        return self.form_repo.update_form(
            user_id=user_id,
            form_id=form_id,
            status=FORM_STATUS.COMPLETED,
            sections=sections,
            completed_at=completed_at,
            updated_at=updated_at
        )
