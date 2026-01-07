from src.shared.domain.entities.field import CheckBoxGroupField, CheckboxField, DateField, DropDownField, FileField, NumberField, RadioGroupField, SwitchButtonField, TextField, TypeAheadField
from src.shared.domain.enums.fields_enum import FIELD_TYPE
from src.shared.domain.enums.file_type_enum import FILE_TYPE
from src.shared.infra.dtos.field_dto import FieldDTO


class Test_FieldDTO:
    def test_field_dto_from_dynamo_text_field(self):
        field_dict = {
            "field_type": "TEXT_FIELD",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "regex": "regex",
            "formatting": "formatting",
            "max_length": 10,
            "value": "value"
        }

        field_dto = FieldDTO.from_dynamo(field_dict)

        assert field_dto.field.field_type == FIELD_TYPE.TEXT_FIELD
        assert field_dto.field.placeholder == "placeholder"
        assert field_dto.field.required == True
        assert field_dto.field.key == "key"
        assert field_dto.field.regex == "regex"
        assert field_dto.field.formatting == "formatting"
        assert field_dto.field.max_length == 10
        assert field_dto.field.value == "value"
    
    def test_field_dto_from_dynamo_number_field(self):
        field_dict = {
            "field_type": "NUMBER_FIELD",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "max_value": 10,
            "min_value": 1,
            "decimal": True,
            "value": 1.0
        }

        field_dto = FieldDTO.from_dynamo(field_dict)

        assert field_dto.field.field_type == FIELD_TYPE.NUMBER_FIELD
        assert field_dto.field.placeholder == "placeholder"
        assert field_dto.field.required == True
        assert field_dto.field.key == "key"
        assert field_dto.field.max_value == 10
        assert field_dto.field.min_value == 1
        assert field_dto.field.decimal == True
        assert field_dto.field.value == 1.0
    
    def test_field_dto_from_dynamo_dropdown_field(self):
        field_dict = {
            "field_type": "DROPDOWN_FIELD",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "options": ["option1", "option2"],
            "value": "option1"
        }

        field_dto = FieldDTO.from_dynamo(field_dict)

        assert field_dto.field.field_type == FIELD_TYPE.DROPDOWN_FIELD
        assert field_dto.field.placeholder == "placeholder"
        assert field_dto.field.required == True
        assert field_dto.field.key == "key"
        assert field_dto.field.options == ["option1", "option2"]
        assert field_dto.field.value == "option1"
    
    def test_field_dto_from_dynamo_typeahead_field(self):
        field_dict = {
            "field_type": "TYPEAHEAD_FIELD",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "options": ["option1", "option2"],
            "max_length": 10,
            "value": "option1"
        }

        field_dto = FieldDTO.from_dynamo(field_dict)

        assert field_dto.field.field_type == FIELD_TYPE.TYPEAHEAD_FIELD
        assert field_dto.field.placeholder == "placeholder"
        assert field_dto.field.required == True
        assert field_dto.field.key == "key"
        assert field_dto.field.options == ["option1", "option2"]
        assert field_dto.field.max_length == 10
        assert field_dto.field.value == "option1"
    
    def test_field_dto_from_dynamo_radio_group_field(self):
        field_dict = {
            "field_type": "RADIO_GROUP_FIELD",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "options": ["option1", "option2"],
            "value": "option1"
        }

        field_dto = FieldDTO.from_dynamo(field_dict)

        assert field_dto.field.field_type == FIELD_TYPE.RADIO_GROUP_FIELD
        assert field_dto.field.placeholder == "placeholder"
        assert field_dto.field.required == True
        assert field_dto.field.key == "key"
        assert field_dto.field.options == ["option1", "option2"]
        assert field_dto.field.value == "option1"
    
    def test_field_dto_from_dynamo_date_field(self):
        field_dict = {
            "field_type": "DATE_FIELD",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "min_date": 123456789,
            "max_date": 987654321,
            "value": 123456789
        }

        field_dto = FieldDTO.from_dynamo(field_dict)

        assert field_dto.field.field_type == FIELD_TYPE.DATE_FIELD
        assert field_dto.field.placeholder == "placeholder"
        assert field_dto.field.required == True
        assert field_dto.field.key == "key"
        assert field_dto.field.min_date == 123456789
        assert field_dto.field.max_date == 987654321
        assert field_dto.field.value == 123456789
    
    def test_field_dto_from_dynamo_checkbox_field(self):
        field_dict = {
            "field_type": "CHECKBOX_FIELD",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "value": True
        }

        field_dto = FieldDTO.from_dynamo(field_dict)

        assert field_dto.field.field_type == FIELD_TYPE.CHECKBOX_FIELD
        assert field_dto.field.placeholder == "placeholder"
        assert field_dto.field.required == True
        assert field_dto.field.key == "key"
        assert field_dto.field.value == True
    
    def test_field_dto_from_dynamo_checkbox_group_field(self):
        field_dict = {
            "field_type": "CHECKBOX_GROUP_FIELD",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "options": ["option1", "option2"],
            "check_limit": 1,
            "value": [True, False]
        }

        field_dto = FieldDTO.from_dynamo(field_dict)

        assert field_dto.field.field_type == FIELD_TYPE.CHECKBOX_GROUP_FIELD
        assert field_dto.field.placeholder == "placeholder"
        assert field_dto.field.required == True
        assert field_dto.field.key == "key"
        assert field_dto.field.options == ["option1", "option2"]
        assert field_dto.field.check_limit == 1
        assert field_dto.field.value == [True, False]
    
    def test_field_dto_from_dynamo_switch_button_field(self):
        field_dict = {
            "field_type": "SWITCH_BUTTON_FIELD",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "value": True
        }

        field_dto = FieldDTO.from_dynamo(field_dict)

        assert field_dto.field.field_type == FIELD_TYPE.SWITCH_BUTTON_FIELD
        assert field_dto.field.placeholder == "placeholder"
        assert field_dto.field.required == True
        assert field_dto.field.key == "key"
        assert field_dto.field.value == True
    
    def test_field_dto_from_dynamo_file_field(self):
        field_dict = {
            "field_type": "FILE_FIELD",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "value": ["value"],
            "file_type": "IMAGE",
            "min_quantity": 1,
            "max_quantity": 2
        }

        field_dto = FieldDTO.from_dynamo(field_dict)

        assert field_dto.field.field_type == FIELD_TYPE.FILE_FIELD
        assert field_dto.field.placeholder == "placeholder"
        assert field_dto.field.required == True
        assert field_dto.field.key == "key"
        assert field_dto.field.value == ["value"]
        assert field_dto.field.file_type == FILE_TYPE.IMAGE
        assert field_dto.field.min_quantity == 1
        assert field_dto.field.max_quantity == 2
    

    def test_field_dto_to_dynamo_text_field(self):
        field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='value')

        field_dto = FieldDTO(field)

        dynamo_dict = field_dto.to_dynamo()

        assert dynamo_dict == {
            "field_type": "TEXT_FIELD",
            "label": "placeholder",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "order": 0,
            "help_text": None,
            "regex": "regex",
            "formatting": "formatting",
            "max_length": 10,
            "value": "value"
        }
    
    def test_field_dto_to_dynamo_number_field(self):
        field = NumberField(placeholder='placeholder', required=True, key='key', max_value=10, min_value=1, decimal=False, value=1.0)

        field_dto = FieldDTO(field)

        dynamo_dict = field_dto.to_dynamo()

        assert dynamo_dict == {
            "field_type": "NUMBER_FIELD",
            "label": "placeholder",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "order": 0,
            "help_text": None,
            "max_value": 10,
            "min_value": 1,
            "decimal": False,
            "value": 1.0
        }
    
    def test_field_dto_to_dynamo_dropdown_field(self):
        field = DropDownField(placeholder='placeholder', required=True, key='key', options=['option1', 'option2'], value='option1')

        field_dto = FieldDTO(field)

        dynamo_dict = field_dto.to_dynamo()

        assert dynamo_dict == {
            "field_type": "DROPDOWN_FIELD",
            "label": "placeholder",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "order": 0,
            "help_text": None,
            "options": ['option1', 'option2'],
            "value": 'option1'
        }
    
    def test_field_dto_to_dynamo_typeahead_field(self):
        field = TypeAheadField(placeholder='placeholder', required=True, key='key', options=['option1', 'option2'], max_length=10, value='option1')

        field_dto = FieldDTO(field)

        dynamo_dict = field_dto.to_dynamo()

        assert dynamo_dict == {
            "field_type": "TYPEAHEAD_FIELD",
            "label": "placeholder",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "order": 0,
            "help_text": None,
            "options": ['option1', 'option2'],
            "max_length": 10,
            "value": 'option1'
        }
    
    def test_field_dto_to_dynamo_radio_group_field(self):
        field = RadioGroupField(placeholder='placeholder', required=True, key='key', options=['option1', 'option2'], value='option1')

        field_dto = FieldDTO(field)

        dynamo_dict = field_dto.to_dynamo()

        assert dynamo_dict == {
            "field_type": "RADIO_GROUP_FIELD",
            "label": "placeholder",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "order": 0,
            "help_text": None,
            "options": ['option1', 'option2'],
            "value": 'option1'
        }
    
    def test_field_dto_to_dynamo_date_field(self):
        field = DateField(placeholder='placeholder', required=True, key='key', min_date=123456789, max_date=987654321, value=123456789)

        field_dto = FieldDTO(field)

        dynamo_dict = field_dto.to_dynamo()

        assert dynamo_dict == {
            "field_type": "DATE_FIELD",
            "label": "placeholder",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "order": 0,
            "help_text": None,
            "min_date": 123456789,
            "max_date": 987654321,
            "value": 123456789
        }
    
    def test_field_dto_to_dynamo_checkbox_field(self):
        field = CheckboxField(placeholder='placeholder', required=True, key='key', value=True)

        field_dto = FieldDTO(field)

        dynamo_dict = field_dto.to_dynamo()

        assert dynamo_dict == {
            "field_type": "CHECKBOX_FIELD",
            "label": "placeholder",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "order": 0,
            "help_text": None,
            "value": True
        }
    
    def test_field_dto_to_dynamo_checkbox_group_field(self):
        field = CheckBoxGroupField(placeholder='placeholder', required=True, key='key', options=['option1', 'option2'], check_limit=1, value=[True, False])

        field_dto = FieldDTO(field)

        dynamo_dict = field_dto.to_dynamo()

        assert dynamo_dict == {
            "field_type": "CHECKBOX_GROUP_FIELD",
            "label": "placeholder",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "order": 0,
            "help_text": None,
            "options": ['option1', 'option2'],
            "check_limit": 1,
            "value": [True, False]
        }
    
    def test_field_dto_to_dynamo_switch_button_field(self):
        field = SwitchButtonField(placeholder='placeholder', required=True, key='key', value=True)

        field_dto = FieldDTO(field)

        dynamo_dict = field_dto.to_dynamo()

        assert dynamo_dict == {
            "field_type": "SWITCH_BUTTON_FIELD",
            "label": "placeholder",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "order": 0,
            "help_text": None,
            "value": True
        }
    
    def test_field_dto_to_dynamo_file_field(self):
        field = FileField(placeholder='placeholder', required=True, key='key', file_type=FILE_TYPE.IMAGE, min_quantity=1, max_quantity=2, value=['value'])

        field_dto = FieldDTO(field)

        dynamo_dict = field_dto.to_dynamo()

        assert dynamo_dict == {
            "field_type": "FILE_FIELD",
            "label": "placeholder",
            "placeholder": "placeholder",
            "required": True,
            "key": "key",
            "order": 0,
            "help_text": None,
            "value": ['value'],
            "file_type": "IMAGE",
            "min_quantity": 1,
            "max_quantity": 2
        }
    
    def test_field_dto_to_entity(self):
        field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='value')

        field_dto = FieldDTO(field)

        assert field_dto.to_entity() == field
    
