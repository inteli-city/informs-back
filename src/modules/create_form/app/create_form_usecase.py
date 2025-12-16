from datetime import datetime, timezone
from typing import List, Optional
import uuid
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import ImageInformationField, InformationField
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.image_repository_interface import IImageRepository
from src.shared.environments import Environments


class CreateFormUsecase:
    def __init__(self, form_repo: IFormRepository, image_repo: IImageRepository):
        self.form_repo = form_repo
        self.image_repo = image_repo

    def __call__(
        self,
        form_title: str,
        creator_user_id: str,
        user_id: str,
        system: str,
        street: str,
        city: str,
        latitude: float,
        longitude: float,
        priority: PRIORITY,
        sections: List[Section],
        justification: Justification,
        number: Optional[int] = None,
        observation: Optional[str] = None,
        expiration_date: Optional[int] = None,
        information_fields: Optional[List[InformationField]] = None,
    ) -> Form:
        
        form_id = str(uuid.uuid4())
        now_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)

        if information_fields:
            for information_field in information_fields:
                if isinstance(information_field, ImageInformationField):
                    image_path = f'{datetime.now(timezone.utc).year}/{form_id}/information_field/{str(uuid.uuid4())}.png'
                    self.image_repo.put_image(base_64_image=information_field.file_path, image_path=image_path)
                    information_field.file_path = f'https://{Environments.get_envs().bucket_name}.s3.sa-east-1.amazonaws.com/{image_path}'

        form = Form(
            form_title=form_title,
            id=form_id,
            created_by=creator_user_id,
            user_id=user_id,
            system=system,
            street=street,
            city=city,
            number=number,
            latitude=latitude,
            longitude=longitude,
            priority=priority,
            status=FORM_STATUS.PENDING,
            created_at=now_timestamp,
            updated_at=now_timestamp,
            sections=sections,
            observation=observation,
            expiration_date=expiration_date,
            justification=justification,
            information_fields=information_fields
        )

        return self.form_repo.create_form(form)
