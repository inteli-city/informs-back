import pytest
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.fields_enum import FIELD_TYPE
from src.shared.domain.enums.file_type_enum import FILE_TYPE
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.infra.dtos.section_dto import SectionDTO


class Test_SectionDTO:

    def test_section_dto_from_request_text(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'TEXT_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'regex': 'regex',
                    'formatting': 'formatting',
                    'max_length': 10,
                    'value': 'value'
                },
            ]
        }

        section = SectionDTO.from_request(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.TEXT_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].regex == 'regex'
        assert section.fields[0].formatting == 'formatting'
        assert section.fields[0].max_length == 10
        assert section.fields[0].value == 'value'
    
    def test_section_dto_from_request_number(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'NUMBER_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'decimal': True,
                    'max_value': 10,
                    'min_value': 10,
                },
            ]
        }

        section = SectionDTO.from_request(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.NUMBER_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].decimal == True
        assert section.fields[0].max_value == 10
        assert section.fields[0].min_value == 10
    
    def test_section_dto_from_request_dropdown(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'DROPDOWN_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'options': ['option1', 'option2']
                },
            ]
        }

        section = SectionDTO.from_request(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.DROPDOWN_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].options == ['option1', 'option2']

    def test_section_dto_from_request_type_ahead(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'TYPEAHEAD_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'options': ['option1', 'option2']
                },
            ]
        }

        section = SectionDTO.from_request(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.TYPEAHEAD_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].options == ['option1', 'option2']
    
    def test_section_dto_from_request_radio_group(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'RADIO_GROUP_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'options': ['option1', 'option2']
                },
            ]
        }

        section = SectionDTO.from_request(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.RADIO_GROUP_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].options == ['option1', 'option2']

    def test_section_dto_from_request_date(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'DATE_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'min_date': 10,
                    'max_date': 10,
                    'value': 10
                },
            ]
        }

        section = SectionDTO.from_request(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.DATE_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].min_date == 10
        assert section.fields[0].max_date == 10
        assert section.fields[0].value == 10

    def test_section_dto_from_request_checkbox(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'CHECKBOX_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'value': True
                },
            ]
        }

        section = SectionDTO.from_request(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.CHECKBOX_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].value == True

    def test_section_dto_from_request_check_box_group(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'CHECKBOX_GROUP_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'options': ['option1', 'option2'],
                    'check_limit': 1
                },
            ]
        }

        section = SectionDTO.from_request(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.CHECKBOX_GROUP_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].options == ['option1', 'option2']
        assert section.fields[0].check_limit == 1

    def test_section_dto_from_request_switch_button(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'SWITCH_BUTTON_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'value': True
                },
            ]
        }

        section = SectionDTO.from_request(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.SWITCH_BUTTON_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].value == True

    def test_section_dto_from_request_file(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'FILE_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'file_type': 'IMAGE',
                    'min_quantity': 1,
                    'max_quantity': 10
                },
            ]
        }

        section = SectionDTO.from_request(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.FILE_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].file_type == FILE_TYPE.IMAGE
        assert section.fields[0].min_quantity == 1
        assert section.fields[0].max_quantity == 10
    
    def test_section_dto_from_request_missing_section_id(self):
        section_dict = {
            'fields': [
                {
                    'field_type': 'TEXT_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'regex': 'regex',
                    'formatting': 'formatting',
                    'max_length': 10,
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_missing_fields(self):
        section_dict = {
            'section_id': '99999'
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_empty_fields(self):
        section_dict = {
            'section_id': '99999',
            'fields': []
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_missing_field_type(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'regex': 'regex',
                    'formatting': 'formatting',
                    'max_length': 10,
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_wrong_field_type(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'WRONG_FIELD_TYPE',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'regex': 'regex',
                    'formatting': 'formatting',
                    'max_length': 10,
                }
            ]
        }

        with pytest.raises(EntityError):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_missing_placeholder(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'TEXT_FIELD',
                    'required': True,
                    'key': 'key',
                    'regex': 'regex',
                    'formatting': 'formatting',
                    'max_length': 10,
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_missing_required(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'TEXT_FIELD',
                    'placeholder': 'placeholder',
                    'key': 'key',
                    'regex': 'regex',
                    'formatting': 'formatting',
                    'max_length': 10,
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_missing_key(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'TEXT_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'regex': 'regex',
                    'formatting': 'formatting',
                    'max_length': 10,
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)

    def test_section_dto_from_request_number_field_missing_decimal(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'NUMBER_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'max_value': 10,
                    'min_value': 10,
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_radio_group_field_missing_options(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'RADIO_GROUP_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_type_ahead_field_missing_options(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'TYPEAHEAD_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_dropdown_field_missing_options(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'DROPDOWN_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_radio_group_field_missing_options(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'RADIO_GROUP_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_check_box_group_field_missing_options(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'CHECKBOX_GROUP_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_file_field_missing_file_type(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'FILE_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_file_field_missing_min_quantity(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'FILE_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'file_type': 'IMAGE',
                    'max_quantity': 10,
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_request_file_field_missing_max_quantity(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'FILE_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'file_type': 'IMAGE',
                    'min_quantity': 10,
                }
            ]
        }

        with pytest.raises(MissingParameters):
            SectionDTO.from_request(section_dict)
    
    def test_section_dto_from_entity(self):
        section = Section(
            section_id=99999,
            fields=[
                TextField(
                    placeholder='placeholder',
                    required=True,
                    key='key',
                    regex='regex',
                    formatting='formatting',
                    max_length=10,
                ),
            ]
        )

        section_dto = SectionDTO.from_entity(section)

        assert section_dto.section_id == '99999'
        assert len(section_dto.fields) == 1
        assert section_dto.fields[0].field_type == FIELD_TYPE.TEXT_FIELD
        assert section_dto.fields[0].placeholder == 'placeholder'
        assert section_dto.fields[0].required == True
        assert section_dto.fields[0].key == 'key'
        assert section_dto.fields[0].regex == 'regex'
        assert section_dto.fields[0].formatting == 'formatting'
        assert section_dto.fields[0].max_length == 10
        assert section_dto.fields[0].value == None
    
    def test_section_from_dynamo(self):
        section_dict = {
            'section_id': '99999',
            'fields': [
                {
                    'field_type': 'TEXT_FIELD',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'regex': 'regex',
                    'formatting': 'formatting',
                    'max_length': 10,
                    'value': 'value'
                },
            ]
        }

        section = SectionDTO.from_dynamo(section_dict)

        assert section.section_id == '99999'
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.TEXT_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].regex == 'regex'
        assert section.fields[0].formatting == 'formatting'
        assert section.fields[0].max_length == 10
        assert section.fields[0].value == 'value'
    
    def test_section_dto_to_dynamo(self):
        section = SectionDTO(
            section_id='99999',
            fields=[
                TextField(
                    placeholder='placeholder',
                    required=True,
                    key='key',
                    regex='regex',
                    formatting='formatting',
                    max_length=10,
                ),
            ]
        )

        section_dynamo = section.to_dynamo()

        assert section_dynamo['section_id'] == '99999'
        assert len(section_dynamo['fields']) == 1
        assert section_dynamo['fields'][0]['field_type'] == FIELD_TYPE.TEXT_FIELD.name
        assert section_dynamo['fields'][0]['label'] == 'placeholder'
        assert section_dynamo['fields'][0]['placeholder'] == 'placeholder'
        assert section_dynamo['fields'][0]['required'] == True
        assert section_dynamo['fields'][0]['key'] == 'key'
        assert section_dynamo['fields'][0]['order'] == 0
        assert section_dynamo['fields'][0]['help_text'] is None
        assert section_dynamo['fields'][0]['regex'] == 'regex'
        assert section_dynamo['fields'][0]['formatting'] == 'formatting'
        assert section_dynamo['fields'][0]['max_length'] == 10
        assert section_dynamo['fields'][0]['value'] == None

    
    def test_section_dto_to_entity(self):
        section_dto = SectionDTO(
            section_id='99999',
            fields=[
                TextField(
                    placeholder='placeholder',
                    required=True,
                    key='key',
                    regex='regex',
                    formatting='formatting',
                    max_length=10,
                ),
            ]
        )

        section = section_dto.to_entity()

        assert section.section_id == 99999
        assert len(section.fields) == 1
        assert section.fields[0].field_type == FIELD_TYPE.TEXT_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].regex == 'regex'
        assert section.fields[0].formatting == 'formatting'
        assert section.fields[0].max_length == 10
        assert section.fields[0].value == None
        
