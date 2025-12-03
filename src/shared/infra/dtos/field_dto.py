from decimal import Decimal
from typing import Dict, Any, Union

from src.shared.domain.entities.field import CheckBoxGroupField, CheckboxField, DateField, DropDownField, Field, FileField, NumberField, RadioGroupField, SwitchButtonField, TextField, TypeAheadField
from src.shared.domain.enums.fields_enum import FIELD_TYPE
from src.shared.domain.enums.file_type_enum import FILE_TYPE
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError

class FieldDTO:
    field: Field

    def __init__(self, field: Field):
        self.field = field
    
    @staticmethod
    def from_dynamo(field_dict: dict):
        if field_dict.get('field_type') is None:
            raise MissingParameters('field_type')
        
        if field_dict.get('field_type') not in [field.value for field in FIELD_TYPE]:
            raise EntityError('field_type')
        
        if field_dict.get('label') is None and field_dict.get('placeholder') is not None:
            field_dict['label'] = field_dict.get('placeholder')
        
        for base_param in ['label', 'required', 'key']:
            if field_dict.get(base_param) is None:
                raise MissingParameters(base_param)
        
        if field_dict.get('order') is None:
            field_dict['order'] = 0

        field_type = FIELD_TYPE[field_dict.get('field_type')]
        label = field_dict.get('label')
        required = bool(field_dict.get('required'))
        key = field_dict.get('key')
        order = int(field_dict.get('order'))
        help_text = field_dict.get('help_text')

        if field_type == FIELD_TYPE.TEXT_FIELD:
            field = TextField(
                label=label,
                required=required,
                key=key,
                order=order,
                regex=field_dict.get('regex'),
                max_length=int(field_dict.get('max_length')) if field_dict.get('max_length') is not None else None,
                value=field_dict.get('value'),
                help_text=help_text
            )

        elif field_type == FIELD_TYPE.NUMBER_FIELD:
            if field_dict.get('decimal') is None:
                raise MissingParameters('decimal')
            field = NumberField(
                label=label,
                required=required,
                key=key,
                order=order,
                decimal=bool(field_dict.get('decimal')) if field_dict.get('decimal') is not None else None,
                max_value=float(field_dict.get('max_value')) if field_dict.get('max_value') is not None else None,
                min_value=float(field_dict.get('min_value')) if field_dict.get('min_value') is not None else None,
                value=float(field_dict.get('value')) if field_dict.get('value') is not None else None,
                help_text=help_text
            )

        elif field_type == FIELD_TYPE.DROPDOWN_FIELD:
            if field_dict.get('options') is None:
                raise MissingParameters('options')
            field = DropDownField(label=label, required=required, key=key, order=order, options=field_dict.get('options'), value=field_dict.get('value'), help_text=help_text)

        elif field_type == FIELD_TYPE.TYPEAHEAD_FIELD:
            if field_dict.get('options') is None:
                raise MissingParameters('options')
            field = TypeAheadField(
                label=label,
                required=required,
                key=key,
                order=order,
                options=field_dict.get('options'),
                max_length=int(field_dict.get('max_length')) if field_dict.get('max_length') is not None else None,
                value=field_dict.get('value'),
                help_text=help_text
            )

        elif field_type == FIELD_TYPE.RADIO_GROUP_FIELD:
            if field_dict.get('options') is None:
                raise MissingParameters('options')
            field = RadioGroupField(label=label, required=required, key=key, order=order, options=field_dict.get('options'), value=field_dict.get('value'), help_text=help_text)

        elif field_type == FIELD_TYPE.DATE_FIELD:
            field = DateField(
                label=label,
                required=required,
                key=key,
                order=order,
                min_date=int(field_dict.get('min_date')) if field_dict.get('min_date') is not None else None,
                max_date=int(field_dict.get('max_date')) if field_dict.get('max_date') is not None else None,
                value=int(field_dict.get('value')) if field_dict.get('value') is not None else None,
                help_text=help_text
            )

        elif field_type == FIELD_TYPE.CHECKBOX_FIELD:
            checkbox_value = field_dict.get('value')
            field = CheckboxField(label=label, required=required, key=key, order=order, value=bool(checkbox_value) if checkbox_value is not None else None, help_text=help_text)

        elif field_type == FIELD_TYPE.CHECKBOX_GROUP_FIELD:
            if field_dict.get('options') is None:
                raise MissingParameters('options')
            field = CheckBoxGroupField(
                label=label,
                required=required,
                key=key,
                order=order,
                options=field_dict.get('options'),
                check_limit=int(field_dict.get('check_limit')) if field_dict.get('check_limit') is not None else None,
                value=[bool(value) for value in field_dict.get('value')] if field_dict.get('value') is not None else None,
                help_text=help_text
            )

        elif field_type == FIELD_TYPE.SWITCH_BUTTON_FIELD:
            switch_value = field_dict.get('value')
            field = SwitchButtonField(label=label, required=required, key=key, order=order, value=bool(switch_value) if switch_value is not None else None, help_text=help_text)

        elif field_type == FIELD_TYPE.FILE_FIELD:
            if field_dict.get('file_type') is None:
                raise MissingParameters('file_type')
            if field_dict.get('file_type') not in [file_type.value for file_type in FILE_TYPE]:
                raise EntityError('file_type')
            if field_dict.get('min_quantity') is None:
                raise MissingParameters('min_quantity')
            if field_dict.get('max_quantity') is None:
                raise MissingParameters('max_quantity')
            field = FileField(
                key=key,
                label=label,
                required=required,
                order=order,
                file_type=FILE_TYPE[field_dict.get('file_type')],
                min_quantity=int(field_dict.get('min_quantity')) if field_dict.get('min_quantity') is not None else None,
                max_quantity=int(field_dict.get('max_quantity')) if field_dict.get('max_quantity') is not None else None,
                value=field_dict.get('value'),
                help_text=help_text
            )
        
        return FieldDTO(field)    

    def to_dynamo(self) -> dict:
        dynamo_dict = {
            "field_type": self.field.field_type.name,
            "label": self.field.label,
            "placeholder": getattr(self.field, "placeholder", None),
            "required": self.field.required,
            "key": self.field.key,
            "order": self.field.order,
            "help_text": self.field.help_text,
        }

        if isinstance(self.field, TextField):
            dynamo_dict.update({
                "regex": self.field.regex,
                "formatting": getattr(self.field, "formatting", None),
                "max_length": self.field.max_length,
                "value": self.field.value
            })
        elif isinstance(self.field, NumberField):
            dynamo_dict.update({
                "max_value": Decimal(str(self.field.max_value)) if self.field.max_value is not None else None,
                "min_value": Decimal(str(self.field.min_value)) if self.field.min_value is not None else None,
                "decimal": self.field.decimal,
                "value": Decimal(str(self.field.value)) if self.field.value is not None else None
            })
        elif isinstance(self.field, DropDownField):
            dynamo_dict.update({
                "options": self.field.options,
                "value": self.field.value
            })
        elif isinstance(self.field, TypeAheadField):
            dynamo_dict.update({
                "options": self.field.options,
                "max_length": Decimal(str(self.field.max_length)) if self.field.max_length is not None else None,
                "value": self.field.value
            })
        elif isinstance(self.field, RadioGroupField):
            dynamo_dict.update({
                "options": self.field.options,
                "value": self.field.value
            })
        elif isinstance(self.field, DateField):
            dynamo_dict.update({
                "min_date": Decimal(str(self.field.min_date)) if self.field.min_date is not None else None,
                "max_date": Decimal(str(self.field.max_date)) if self.field.max_date is not None else None,
                "value": self.field.value
            })
        elif isinstance(self.field, CheckboxField):
            dynamo_dict.update({
                "value": self.field.value
            })
        elif isinstance(self.field, CheckBoxGroupField):
            dynamo_dict.update({
                "options": self.field.options,
                "check_limit": Decimal(str(self.field.check_limit)) if self.field.check_limit is not None else None,
                "value": self.field.value
            })
        elif isinstance(self.field, SwitchButtonField):
            dynamo_dict.update({
                "value": self.field.value
            })
        elif isinstance(self.field, FileField):
            dynamo_dict.update({
                "file_type": self.field.file_type.name,
                "min_quantity": Decimal(str(self.field.min_quantity)) if self.field.min_quantity is not None else None,
                "max_quantity": Decimal(str(self.field.max_quantity)) if self.field.max_quantity is not None else None,
                "value": self.field.value
            })

        return dynamo_dict

    def to_entity(self) -> Field:
        return self.field
