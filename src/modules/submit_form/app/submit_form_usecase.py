from typing import List, Optional
import uuid
from datetime import datetime
from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.image_upload import ImageUpload
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.image_repository_interface import IImageRepository
from src.shared.domain.repositories.queue_repository_interface import IQueueRepository
from src.shared.helpers.functions.s3_url import build_s3_url
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


class SubmitFormUsecase:

    def __init__(self, form_repo: IFormRepository, image_repo: IImageRepository, queue_repo: IQueueRepository):
        self.form_repo = form_repo
        self.image_repo = image_repo
        self.queue_repo = queue_repo
    
    def __call__(
        self,
        user_id: str,
        form_id: str,
        sections: List[Section],
        completed_at: int,
        file_uploads: Optional[dict] = None,
    ) -> list[ImageUpload]:
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
        
        images: list[ImageUpload] = []
        for section in sections:
            for field in section.fields:
                if isinstance(field, FileField) and field.value is not None:
                    uploads = None
                    if file_uploads is not None:
                        uploads = file_uploads.get((section.section_id, field.key))
                    if not uploads:
                        raise EntityError("mimetype")
                    image_urls = []
                    for idx, upload in enumerate(uploads):
                        mimetype = upload.get("mimetype") or upload.get("mimetype")
                        filename = upload.get("filename")
                        if not isinstance(mimetype, str) or not mimetype:
                            raise EntityError("mimetype")
                        image_path = f'{datetime.now().year}/{form_id}/sections/{section.section_id}/{str(uuid.uuid4())}.{mimetype.split("/")[-1]}'
                        presigned_url = self.image_repo.generate_presigned_url(
                            image_path=image_path,
                            mimetype=mimetype,
                        )
                        image_url = build_s3_url(image_path)
                        image_urls.append(image_url)
                        images.append(
                            ImageUpload(
                                filename=filename,
                                mimetype=mimetype,
                                pre_signed_url=presigned_url,
                                image_path=image_path,
                                image_url=image_url,
                                section_id=section.section_id,
                                field_key=field.key,
                                file_index=idx,
                            )
                        )
                    field.value = image_urls[0] if len(image_urls) == 1 else image_urls
        
        updated_at = int(datetime.now().timestamp() * 1000)
        
        updated_form = self.form_repo.update_form(
            user_id=user_id,
            form_id=form_id,
            status=FORM_STATUS.COMPLETED,
            sections=sections,
            completed_at=completed_at,
            updated_at=updated_at
        )
        
        self.queue_repo.send_form(updated_form)
        return images
