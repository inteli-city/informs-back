from datetime import datetime
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
from src.shared.helpers.errors.usecase_errors import ForbiddenAction


class CreateFormUsecase:
    def __init__(self, form_repo: IFormRepository, image_repo: IImageRepository):
        self.form_repo = form_repo
        self.image_repo = image_repo

    def __call__(self,
                    form_title: str,
                    creator_user_id: str,
                    user_id: str,
                    vinculation_form_id: Optional[str],
                    can_vinculate: bool,
                    template: str,
                    area: str,
                    system: str,
                    street: str,
                    city: str,
                    number: int,
                    latitude: float,
                    longitude: float,
                    region: str,
                    description: Optional[str],
                    priority: PRIORITY,
                    expiration_date: int,
                    justification: Justification,
                    comments: Optional[str],
                    sections: List[Section],
                    information_fields: Optional[List[InformationField]]
                 ) -> Form:
        
        form_id = str(uuid.uuid4())

        for information_field in information_fields:
            if isinstance(information_field, ImageInformationField):
                image_path = f'{datetime.now().year}/{form_id}/information_field/{str(uuid.uuid4())}.png'
                self.image_repo.put_image(base_64_image=information_field.file_path, image_path=image_path)
                information_field.file_path = f'https://{Environments.get_envs().bucket_name}.s3.sa-east-1.amazonaws.com/{image_path}'

        form = Form(
            form_title=form_title,
            form_id=form_id,
            creator_user_id=creator_user_id,
            user_id=user_id,
            vinculation_form_id=vinculation_form_id,
            can_vinculate=can_vinculate,
            template=template,
            area=area,
            system=system,
            street=street,
            city=city,
            number=number,
            latitude=latitude,
            longitude=longitude,
            region=region,
            description=description,
            priority=priority,
            status=FORM_STATUS.NOT_STARTED,
            expiration_date=expiration_date,
            creation_date=int(datetime.now().timestamp()),
            start_date=None,
            conclusion_date=None,
            justification=justification,
            comments=comments,
            sections=sections,
            information_fields=information_fields
        )

        return self.form_repo.create_form(form)