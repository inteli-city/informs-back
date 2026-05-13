import os
import sys

sys.path.append(os.getcwd())

from src.modules.create_form.app.create_form_viewmodel import FieldViewmodel, SectionViewmodel, JustificationViewmodel, FormViewmodel, CreateFormViewmodel
from src.shared.domain.entities.field import TextField, FileField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import TextInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority


class Test_CreateFormViewmodel:
    def _make_form(self):
        field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='value')
        section = Section(section_id=1, fields=[field])
        justification = Justification(options=[JustificationOption(option='option', required_image=True, required_text=True)])
        return Form(
            id='d61dbf66-a10f-11ed-a8fc-0242ac120010',
            form_title='FORM_TITLE',
            created_by='d61dbf66-a10f-11ed-a8fc-0242ac120001',
            user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
            template=None,
            system='GAIA',
            city='1',
            area=None,
            street='1',
            number=1,
            latitude=1.0,
            longitude=1.0,
            priority=Priority.EMERGENCY,
            status=FormStatus.PENDING,
            expiration_date=946407600000,
            observation=None,
            created_at=946407600000,
            updated_at=946407600000,
            justification=justification,
            sections=[section],
            information_fields=[TextInformationField(value='value')]
        )

    def test_field_viewmodel(self):
        viewmodel = FieldViewmodel(field=TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='value'))
        response = viewmodel.to_dict()
        assert response["field_type"] == "TEXT_FIELD"
        assert response["label"] == "placeholder"
        assert response["required"] is True
        assert response["regex"] == "regex"
        assert response["max_length"] == 10

    def test_field_viewmodel_file(self):
        viewmodel = FieldViewmodel(field=FileField(placeholder='placeholder', required=True, key='key', file_type=FileType.IMAGE, min_quantity=1, max_quantity=10, value=['value']))
        response = viewmodel.to_dict()
        assert response["file_type"] == "IMAGE"
        assert response["min_quantity"] == 1
        assert response["max_quantity"] == 10

    def test_section_viewmodel(self):
        field = TextField(placeholder='placeholder', required=True, key='key', regex=None, formatting=None, max_length=None, value=None)
        section = Section(section_id=1, fields=[field])
        vm = SectionViewmodel(section)
        result = vm.to_dict()
        assert result["section_id"] == 1
        assert len(result["fields"]) == 1

    def test_justification_viewmodel(self):
        justification = Justification(options=[JustificationOption(option='option', required_image=True, required_text=True)])
        vm = JustificationViewmodel(justification)
        result = vm.to_dict()
        assert result["options"][0]["option"] == "option"
        assert result["selected"] is None

    def test_form_viewmodel(self):
        form = self._make_form()
        vm = FormViewmodel(form)
        result = vm.to_dict()
        assert result["id"] == form.id
        assert result["status"] == form.status.value
        assert result["priority"] == int(form.priority.value)
        assert len(result["sections"]) == 1

    def test_create_form_viewmodel(self):
        form = self._make_form()
        vm = CreateFormViewmodel(form)
        result = vm.to_dict()
        assert result["id"] == form.id
        assert result["created_by"] == form.created_by
        assert result["files"] == []
