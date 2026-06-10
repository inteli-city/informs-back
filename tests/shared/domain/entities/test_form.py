import pytest

from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import FileInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.errors.domain_errors import EntityError


valid_id = 'd61dbf66-a10f-11ed-a8fc-0242ac120001'
text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='value')
section = Section(section_id=1, fields=[text_field])
information_field = FileInformationField(file_path='file')
justification_option = JustificationOption(option='option', required_image=True, required_text=True)
justification = Justification(
    options=[justification_option],
    selected=SelectedJustification(option='option', text='text', image_url='image')
)


def make_form(**overrides):
    base = dict(
        id=valid_id,
        form_title='form_title',
        created_by=valid_id,
        user_id=valid_id,
        system='system',
        city='city',
        street='street',
        latitude=1.0,
        longitude=1.0,
        priority=Priority.LOW,
        status=FormStatus.PENDING,
        created_at=1,
        updated_at=1,
        sections=[section],
    )
    base.update(overrides)
    return Form(**base)


class Test_Form:

    def test_form_valid(self):
        make_form(
            template='template',
            area='area',
            number=123,
            observation='obs',
            expiration_date=946407600000,
            justification=justification,
            information_fields=[information_field],
            in_progress_at=None,
            cancelled_at=None,
            completed_at=None,
        )

    def test_invalid_id(self):
        with pytest.raises(EntityError):
            make_form(id='short')

    def test_invalid_priority_type(self):
        with pytest.raises(EntityError):
            make_form(priority='1')  # not enum

    def test_sections_required(self):
        with pytest.raises(EntityError):
            make_form(sections=[])

    def test_sections_empty_list_with_uuid_template(self):
        form = make_form(template=valid_id, justification=justification, sections=[])
        assert form.sections == []

    def test_information_fields_type(self):
        with pytest.raises(EntityError):
            make_form(information_fields=['invalid'])

    def test_information_fields_empty_list(self):
        form = make_form(justification=justification, information_fields=[])
        assert form.information_fields == []

    def test_justification_type(self):
        with pytest.raises(EntityError):
            make_form(justification='not_valid')
