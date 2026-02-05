import abc
from typing import List, Optional, Union

from src.shared.domain.enums.fields_enum import FIELD_TYPE
from src.shared.domain.enums.file_type_enum import FILE_TYPE
from src.shared.helpers.errors.domain_errors import EntityError


class Field(abc.ABC):
    field_type: FIELD_TYPE
    label: str
    required: bool
    key: str
    order: int
    help_text: Optional[str]

    @abc.abstractmethod
    def __init__(self, field_type: FIELD_TYPE, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, help_text: Optional[str] = None, placeholder: Optional[str] = None):
        if not isinstance(field_type, FIELD_TYPE):
            raise EntityError('field_type')
        self.field_type = field_type

        label_value = label if label is not None else placeholder
        if not isinstance(label_value, str):
            raise EntityError('label')
        self.label = label_value
        self.placeholder = label_value  # compatibility alias

        if not isinstance(required, bool):
            raise EntityError('required')
        self.required = required

        if not isinstance(key, str):
            raise EntityError('key')
        self.key = key

        if not isinstance(order, int):
            raise EntityError('order')
        self.order = order

        if help_text is not None and not isinstance(help_text, str):
            raise EntityError('help_text')
        self.help_text = help_text

    def to_legacy_dict(self) -> dict:
        return {
            "field_type": self.field_type.name,
            "placeholder": self.label,
            "required": self.required,
            "key": self.key,
        }


class TextField(Field):
    max_length: Optional[int]
    value: Optional[str]
    regex: Optional[str]
    formatting: Optional[str]

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, regex: Optional[str] = None, max_length: Optional[int] = None, value: Optional[str] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None, formatting: Optional[str] = None):
        super().__init__(FIELD_TYPE.TEXT_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if regex is not None and not isinstance(regex, str):
            raise EntityError('regex')
        self.regex = regex
        self.formatting = formatting

        if max_length is not None and not isinstance(max_length, int):
            raise EntityError('max_length')
        self.max_length = max_length

        if value is not None:
            if not isinstance(value, str):
                raise EntityError('value')
            if max_length is not None and len(value) > max_length:
                raise EntityError('value')
        self.value = value

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({
            "regex": self.regex,
            "formatting": self.formatting,
            "max_length": self.max_length,
            "value": self.value
        })
        return base


class NumberField(Field):
    max_value: Optional[Union[int, float]]
    min_value: Optional[Union[int, float]]
    decimal: Optional[bool]
    value: Optional[Union[int, float]]

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, decimal: Optional[bool] = None, max_value: Optional[Union[int, float]] = None, min_value: Optional[Union[int, float]] = None, value: Optional[Union[int, float]] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None):
        super().__init__(FIELD_TYPE.NUMBER_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if decimal is not None and not isinstance(decimal, bool):
            raise EntityError('decimal')
        self.decimal = decimal

        if max_value is not None and not isinstance(max_value, (int, float)):
            raise EntityError('max_value')
        self.max_value = max_value

        if min_value is not None and not isinstance(min_value, (int, float)):
            raise EntityError('min_value')
        self.min_value = min_value

        if value is not None:
            if not isinstance(value, (int, float)):
                raise EntityError('value')
            if min_value is not None and value < min_value:
                raise EntityError('value')
            if max_value is not None and value > max_value:
                raise EntityError('value')
            if decimal is False and isinstance(value, float) and not value.is_integer():
                raise EntityError('value')
        self.value = value

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({
            "max_value": self.max_value,
            "min_value": self.min_value,
            "decimal": self.decimal,
            "value": self.value
        })
        return base


class DropDownField(Field):
    options: List[str]
    value: Optional[str]

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, options: List[str] = None, value: Optional[str] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None):
        super().__init__(FIELD_TYPE.DROPDOWN_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if not isinstance(options, list) or not options or not all(isinstance(option, str) for option in options):
            raise EntityError('options')
        self.options = options

        if value is not None and (not isinstance(value, str) or value not in options):
            raise EntityError('value')
        self.value = value

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({
            "options": self.options,
            "value": self.value
        })
        return base


class TypeAheadField(Field):
    options: List[str]
    max_length: Optional[int]
    value: Optional[str]

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, options: List[str] = None, max_length: Optional[int] = None, value: Optional[str] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None):
        super().__init__(FIELD_TYPE.TYPEAHEAD_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if not isinstance(options, list) or not options or not all(isinstance(option, str) for option in options):
            raise EntityError('options')
        self.options = options

        if max_length is not None and not isinstance(max_length, int):
            raise EntityError('max_length')
        self.max_length = max_length

        if value is not None and not isinstance(value, str):
            raise EntityError('value')
        self.value = value

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({
            "options": self.options,
            "max_length": self.max_length,
            "value": self.value
        })
        return base


class RadioGroupField(Field):
    options: List[str]
    value: Optional[str]

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, options: List[str] = None, value: Optional[str] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None):
        super().__init__(FIELD_TYPE.RADIO_GROUP_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if not isinstance(options, list) or not options or not all(isinstance(option, str) for option in options):
            raise EntityError('options')
        self.options = options

        if value is not None and (not isinstance(value, str) or value not in options):
            raise EntityError('value')
        self.value = value

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({
            "options": self.options,
            "value": self.value
        })
        return base


class DateField(Field):
    min_date: Optional[int]  # timestamp
    max_date: Optional[int]  # timestamp
    value: Optional[int]  # timestamp

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, min_date: Optional[int] = None, max_date: Optional[int] = None, value: Optional[int] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None):
        super().__init__(FIELD_TYPE.DATE_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if min_date is not None and not isinstance(min_date, int):
            raise EntityError('min_date')
        self.min_date = min_date

        if max_date is not None and not isinstance(max_date, int):
            raise EntityError('max_date')
        self.max_date = max_date

        if value is not None:
            if not isinstance(value, int):
                raise EntityError('value')
            if min_date is not None and value < min_date:
                raise EntityError('value')
            if max_date is not None and value > max_date:
                raise EntityError('value')
        self.value = value

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({
            "min_date": self.min_date,
            "max_date": self.max_date,
            "value": self.value
        })
        return base


class CheckboxField(Field):
    value: Optional[bool]

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, value: Optional[bool] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None):
        super().__init__(FIELD_TYPE.CHECKBOX_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if value is not None and not isinstance(value, bool):
            raise EntityError('value')
        self.value = value

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({"value": self.value})
        return base


class CheckBoxGroupField(Field):
    options: List[str]
    check_limit: Optional[int]
    value: Optional[List[bool]]

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, options: List[str] = None, check_limit: Optional[int] = None, value: Optional[List[bool]] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None):
        super().__init__(FIELD_TYPE.CHECKBOX_GROUP_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if not isinstance(options, list) or not options or not all(isinstance(option, str) for option in options):
            raise EntityError('options')
        self.options = options

        if check_limit is not None:
            if not isinstance(check_limit, int):
                raise EntityError('check_limit')
            if check_limit > len(options):
                raise EntityError('check_limit')
        self.check_limit = check_limit

        if value is not None:
            if not isinstance(value, list) or len(value) != len(options) or not all(isinstance(val, bool) for val in value):
                raise EntityError('value')
            if check_limit is not None and sum(value) > check_limit:
                raise EntityError('value')
        self.value = value

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({
            "options": self.options,
            "check_limit": self.check_limit,
            "value": self.value
        })
        return base


class SwitchButtonField(Field):
    value: Optional[bool]

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, value: Optional[bool] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None):
        super().__init__(FIELD_TYPE.SWITCH_BUTTON_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if value is not None and not isinstance(value, bool):
            raise EntityError('value')
        self.value = value

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({"value": self.value})
        return base


class FileField(Field):
    file_type: FILE_TYPE
    min_quantity: Optional[int]
    max_quantity: Optional[int]
    value: Optional[Union[List[str], str, dict]]

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, file_type: FILE_TYPE = None, min_quantity: Optional[int] = None, max_quantity: Optional[int] = None, value: Optional[Union[List[str], str, dict]] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None):
        super().__init__(FIELD_TYPE.FILE_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if not isinstance(file_type, FILE_TYPE):
            raise EntityError('file_type')
        self.file_type = file_type

        if min_quantity is not None and not isinstance(min_quantity, int):
            raise EntityError('min_quantity')
        self.min_quantity = min_quantity

        if max_quantity is not None and not isinstance(max_quantity, int):
            raise EntityError('max_quantity')
        self.max_quantity = max_quantity

        if self.min_quantity is not None and self.max_quantity is not None and self.min_quantity > self.max_quantity:
            raise EntityError('min_quantity')

        if value is not None:
            if isinstance(value, list):
                if not all(isinstance(item, (str, dict)) for item in value):
                    raise EntityError('value')
                if self.min_quantity is not None and len(value) < self.min_quantity:
                    raise EntityError('value')
                if self.max_quantity is not None and len(value) > self.max_quantity:
                    raise EntityError('value')
            elif not isinstance(value, (str, dict)):
                raise EntityError('value')
        self.value = value

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({
            "file_type": self.file_type.name,
            "min_quantity": self.min_quantity,
            "max_quantity": self.max_quantity,
            "value": self.value
        })
        return base
