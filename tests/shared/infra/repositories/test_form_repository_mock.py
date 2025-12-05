import pytest
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import ImageInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.helpers.errors.usecase_errors import DuplicatedItem
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock

justification_option = JustificationOption(option='option', required_image=True, required_text=True)
justification = Justification(
    options=[justification_option],
    selected=SelectedJustification(option='option', text='text', image_url='image')
)

class Test_FormRepositoryMock:

    def test_form_repository_mock_get_form_by_id(self):
        repo = FormRepositoryMock()
        form = repo.get_form_by_id(user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001', form_id=repo.forms[0].id)

        assert form.id == repo.forms[0].id
    
    def test_form_repository_mock_get_form_by_id_not_found(self):
        repo = FormRepositoryMock()
        form = repo.get_form_by_id(user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001', form_id='d61dbf66-a10f-11ed-a8fc-0242ac120099')

        assert form is None

    def test_form_repository_mock_get_form_by_user_id(self):
        repo = FormRepositoryMock()
        form = repo.get_form_by_user_id(repo.forms[0].user_id)

        assert len(form) == 2

    def test_form_repository_mock_create_form(self):
        repo = FormRepositoryMock()
        text_field = TextField(label='label', required=True, key='key', order=1, regex='regex', max_length=10, value='value')
        section = Section(section_id=1, fields=[text_field, text_field])
        information_field = ImageInformationField(file_path='value')
        form_to_create = Form(
            id='d61dbf66-a10f-11ed-a8fc-0242ac120013',
            form_title='FORM TITLE',
            created_by='d61dbf66-a10f-11ed-a8fc-0242ac120001',
            user_id='d61dbf66-a10f-11ed-a8fc-0242ac120002',
            template='TEMPLATE',
            area='1',
            system='GAIA',
            street='1',
            city='1',
            number=1,
            latitude=1.0,
            longitude=1.0,
            priority=PRIORITY.EMERGENCY,
            status=FORM_STATUS.COMPLETED,
            expiration_date=946407600000,
            created_at=946407600000,
            updated_at=946407600000,
            in_progress_at=946407600000,
            cancelled_at=None,
            completed_at=946407600000,
            justification=justification,
            sections=[section],
            information_fields=[
                information_field,
                information_field,
            ]
        )

        form = repo.create_form(
            form=form_to_create
        )

        assert form.id == 'd61dbf66-a10f-11ed-a8fc-0242ac120013'

    def test_form_repository_mock_create_form_duplicated_form_id(self):
        repo = FormRepositoryMock()
        with pytest.raises(DuplicatedItem):
            repo.create_form(repo.forms[0])
    
    def test_form_repository_mock_update_form_status(self):
        repo = FormRepositoryMock()
        form = repo.update_form(user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001', form_id=repo.forms[0].id, status=FORM_STATUS.IN_PROGRESS, updated_at=1)

        assert form.status == FORM_STATUS.IN_PROGRESS
    
    def test_form_repository_mock_cancel_form(self):
        repo = FormRepositoryMock()
        form = repo.cancel_form(user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001', form_id=repo.forms[0].id, justification=justification, cancelled_at=1, updated_at=1)

        assert form.status == FORM_STATUS.CANCELLED
        assert form.justification.selected.option == 'option'
        assert form.justification.selected.text == 'text'
        assert form.justification.selected.image_url == 'image'
    
    def test_form_repository_mock_complete_form(self):
        repo = FormRepositoryMock()
        text_field = TextField(label='label', required=True, key='key', order=1, regex='regex', max_length=10, value='value')
        section = Section(section_id=2, fields=[text_field, text_field])
        form = repo.complete_form('d61dbf66-a10f-11ed-a8fc-0242ac120001', repo.forms[0].id, [section], completed_at=1, updated_at=1)

        assert form.status == FORM_STATUS.COMPLETED
        assert form.sections == [section]
