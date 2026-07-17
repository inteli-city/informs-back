import pytest
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.fields_enum import FieldType
from src.shared.domain.enums.file_type_enum import FileType
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
        assert section.fields[0].field_type == FieldType.TEXT_FIELD
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
        assert section.fields[0].field_type == FieldType.NUMBER_FIELD
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
        assert section.fields[0].field_type == FieldType.DROPDOWN_FIELD
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
        assert section.fields[0].field_type == FieldType.TYPEAHEAD_FIELD
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
        assert section.fields[0].field_type == FieldType.RADIO_GROUP_FIELD
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
        assert section.fields[0].field_type == FieldType.DATE_FIELD
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
        assert section.fields[0].field_type == FieldType.CHECKBOX_FIELD
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
        assert section.fields[0].field_type == FieldType.CHECKBOX_GROUP_FIELD
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
        assert section.fields[0].field_type == FieldType.SWITCH_BUTTON_FIELD
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
        assert section.fields[0].field_type == FieldType.FILE_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].file_type == FileType.IMAGE
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
        assert section_dto.fields[0].field_type == FieldType.TEXT_FIELD
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
        assert section.fields[0].field_type == FieldType.TEXT_FIELD
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
        assert section_dynamo['fields'][0]['field_type'] == FieldType.TEXT_FIELD.name
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
        assert section.fields[0].field_type == FieldType.TEXT_FIELD
        assert section.fields[0].placeholder == 'placeholder'
        assert section.fields[0].required == True
        assert section.fields[0].key == 'key'
        assert section.fields[0].regex == 'regex'
        assert section.fields[0].formatting == 'formatting'
        assert section.fields[0].max_length == 10
        assert section.fields[0].value == None

    # --- Novos testes: is_duplicable e section_instance ---

    def test_section_dto_from_request_is_duplicable_true(self):
        section_dict = {
            'section_id': '1',
            'is_duplicable': True,
            'fields': [{'field_type': 'TEXT_FIELD', 'placeholder': 'x', 'required': True, 'key': 'k', 'max_length': 10}],
        }
        dto = SectionDTO.from_request(section_dict)
        assert dto.is_duplicable is True
        assert dto.section_instance == 0

    def test_section_dto_from_request_section_instance_nonzero_raises(self):
        """section_instance só é materializado na submissão (Form._materialize_section_instance);
        aceitar um valor != 0 na criação/atualização deixaria a seção sem instância 0 correspondente."""
        section_dict = {
            'section_id': '1',
            'is_duplicable': True,
            'section_instance': 3,
            'fields': [{'field_type': 'TEXT_FIELD', 'placeholder': 'x', 'required': True, 'key': 'k', 'max_length': 10}],
        }
        with pytest.raises(EntityError):
            SectionDTO.from_request(section_dict)

    def test_section_dto_from_request_is_duplicable_default_false(self):
        section_dict = {
            'section_id': '1',
            'fields': [{'field_type': 'TEXT_FIELD', 'placeholder': 'x', 'required': True, 'key': 'k', 'max_length': 10}],
        }
        dto = SectionDTO.from_request(section_dict)
        assert dto.is_duplicable is False

    def test_section_dto_from_entity_preserves_flags(self):
        from src.shared.domain.entities.field import TextField as TF
        section = Section(section_id=5, fields=[TF(label='l', required=True, key='k', order=1, max_length=5)], is_duplicable=True, section_instance=2)
        dto = SectionDTO.from_entity(section)
        assert dto.is_duplicable is True
        assert dto.section_instance == 2

    def test_section_dto_from_dynamo_defaults_when_missing(self):
        """Retrocompatibilidade: seções antigas no DynamoDB sem esses campos."""
        section_dict = {
            'section_id': '1',
            'fields': [{'field_type': 'TEXT_FIELD', 'placeholder': 'x', 'required': True, 'key': 'k', 'max_length': 10}],
        }
        dto = SectionDTO.from_dynamo(section_dict)
        assert dto.is_duplicable is False
        assert dto.section_instance == 0

    def test_section_dto_from_dynamo_with_flags(self):
        section_dict = {
            'section_id': '1',
            'is_duplicable': True,
            'section_instance': 3,
            'fields': [{'field_type': 'TEXT_FIELD', 'placeholder': 'x', 'required': True, 'key': 'k', 'max_length': 10}],
        }
        dto = SectionDTO.from_dynamo(section_dict)
        assert dto.is_duplicable is True
        assert dto.section_instance == 3

    def test_section_dto_to_dynamo_includes_flags(self):
        from src.shared.domain.entities.field import TextField as TF
        dto = SectionDTO(
            section_id='1',
            fields=[TF(label='l', required=True, key='k', order=1, max_length=5)],
            is_duplicable=True,
            section_instance=1,
        )
        result = dto.to_dynamo()
        assert result['is_duplicable'] is True
        assert result['section_instance'] == 1

    def test_section_dto_to_entity_preserves_flags(self):
        from src.shared.domain.entities.field import TextField as TF
        dto = SectionDTO(
            section_id='7',
            fields=[TF(label='l', required=True, key='k', order=1, max_length=5)],
            is_duplicable=True,
            section_instance=2,
        )
        entity = dto.to_entity()
        assert entity.section_id == 7
        assert entity.is_duplicable is True
        assert entity.section_instance == 2

