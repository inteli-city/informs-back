import os
import sys
from datetime import datetime

sys.path.append(os.getcwd())

from src.modules.create_form.app.create_form_usecase import CreateFormUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.information_field import ImageInformationField, TextInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.image_repository_mock import ImageRepositoryMock


class Test_CreateFormUsecase:
    def test_create_form_usecase(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='value')
        section = Section(section_id=1, fields=[text_field])
        justification = Justification(
            options=[JustificationOption(option='option', required_image=True, required_text=True)]
        )

        form, images = usecase(
            form_title='FORM TITLE',
            creator_user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
            user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
            system='GAIA',
            street='1',
            city='1',
            latitude=1.0,
            longitude=1.0,
            priority=PRIORITY.EMERGENCY,
            sections=[section],
            justification=justification,
            information_fields=[TextInformationField(value='info')],
            observation='obs',
            expiration_date=946407600000
        )

        assert len(form.id) == 36
        assert form.status == FORM_STATUS.PENDING
        assert form.priority == PRIORITY.EMERGENCY
        assert form.observation == 'obs'
        assert form.expiration_date == 946407600000
        assert form.sections[0].section_id == 1
        assert isinstance(form.information_fields[0], TextInformationField)
        assert images == []

    def test_create_form_usecase_with_images(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='value')
        section = Section(section_id=1, fields=[text_field])
        justification = Justification(
            options=[JustificationOption(option='option', required_image=True, required_text=True)]
        )

        form, images = usecase(
            form_title='FORM TITLE',
            creator_user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
            user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
            system='GAIA',
            street='1',
            city='1',
            latitude=1.0,
            longitude=1.0,
            priority=PRIORITY.EMERGENCY,
            sections=[section],
            justification=justification,
            information_fields=[ImageInformationField(file_path="")],
            information_fields_uploads=[{"filename": "a.jpg", "mimetype": "image/jpeg"}],
        )

        assert form.information_fields[0].file_path.startswith("https://")
        assert len(images) == 1
        assert images[0].filename == "a.jpg"
        assert images[0].mimetype == "image/jpeg"
