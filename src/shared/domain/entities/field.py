import abc
from copy import deepcopy
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
            raise EntityError('Tipo de campo inválido')
        self.field_type = field_type

        label_value = label if label is not None else placeholder
        if not isinstance(label_value, str):
            raise EntityError('Rótulo do campo deve ser uma string não vazia')
        self.label = label_value
        self.placeholder = label_value  # compatibility alias

        if not isinstance(required, bool):
            raise EntityError("Campo 'required' deve ser verdadeiro ou falso")
        self.required = required

        if not isinstance(key, str):
            raise EntityError('Chave do campo deve ser uma string')
        self.key = key

        if not isinstance(order, int):
            raise EntityError('Ordem do campo deve ser um número inteiro')
        self.order = order

        if help_text is not None and not isinstance(help_text, str):
            raise EntityError('Texto de ajuda deve ser uma string')
        self.help_text = help_text

    def to_legacy_dict(self) -> dict:
        return {
            "field_type": self.field_type.name,
            "placeholder": self.label,
            "required": self.required,
            "key": self.key,
        }

    def normalize_value(self, value):
        self._validate_value(value)
        return value

    def _validate_value(self, value):
        return None

    def set_value(self, value):
        if not hasattr(self, "value"):
            raise EntityError("Campo nao aceita valor")
        self.value = self.normalize_value(value)

    def with_value(self, value):
        field = deepcopy(self)
        field.set_value(value)
        return field


class TextField(Field):
    max_length: Optional[int]
    value: Optional[str]
    regex: Optional[str]
    formatting: Optional[str]

    def __init__(self, label: Optional[str] = None, required: Optional[bool] = None, key: Optional[str] = None, order: int = 0, regex: Optional[str] = None, max_length: Optional[int] = None, value: Optional[str] = None, help_text: Optional[str] = None, placeholder: Optional[str] = None, formatting: Optional[str] = None):
        super().__init__(FIELD_TYPE.TEXT_FIELD, label, required, key, order, help_text, placeholder=placeholder)
        if regex is not None and not isinstance(regex, str):
            raise EntityError('Expressão regular deve ser uma string')
        self.regex = regex
        self.formatting = formatting

        if max_length is not None and not isinstance(max_length, int):
            raise EntityError('Comprimento máximo deve ser um número inteiro')
        self.max_length = max_length

        if value is not None:
            if not isinstance(value, str):
                raise EntityError('Valor do campo de texto deve ser uma string')
            if max_length is not None and len(value) > max_length:
                raise EntityError(f'Valor excede o comprimento máximo de {max_length} caracteres')
        self.value = value

    def _validate_value(self, value):
        if value is not None:
            if not isinstance(value, str):
                raise EntityError('Valor do campo de texto deve ser uma string')
            if self.max_length is not None and len(value) > self.max_length:
                raise EntityError(f'Valor excede o comprimento máximo de {self.max_length} caracteres')

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
            raise EntityError("Campo 'decimal' deve ser verdadeiro ou falso")
        self.decimal = decimal

        if max_value is not None and not isinstance(max_value, (int, float)):
            raise EntityError('Valor máximo deve ser um número')
        self.max_value = max_value

        if min_value is not None and not isinstance(min_value, (int, float)):
            raise EntityError('Valor mínimo deve ser um número')
        self.min_value = min_value

        if value is not None:
            if not isinstance(value, (int, float)):
                raise EntityError('Valor numérico deve ser um número')
            if min_value is not None and value < min_value:
                raise EntityError(f'Valor {value} é menor que o mínimo permitido ({min_value})')
            if max_value is not None and value > max_value:
                raise EntityError(f'Valor {value} é maior que o máximo permitido ({max_value})')
            if decimal is False and isinstance(value, float) and not value.is_integer():
                raise EntityError('Valor não pode ser decimal para este campo')
        self.value = value

    def normalize_value(self, value):
        if value is None:
            return None
        try:
            normalized_value = float(value)
        except (TypeError, ValueError):
            raise EntityError('Valor numérico deve ser um número')
        self._validate_value(normalized_value)
        return normalized_value

    def _validate_value(self, value):
        if value is not None:
            if not isinstance(value, (int, float)):
                raise EntityError('Valor numérico deve ser um número')
            if self.min_value is not None and value < self.min_value:
                raise EntityError(f'Valor {value} é menor que o mínimo permitido ({self.min_value})')
            if self.max_value is not None and value > self.max_value:
                raise EntityError(f'Valor {value} é maior que o máximo permitido ({self.max_value})')
            if self.decimal is False and isinstance(value, float) and not value.is_integer():
                raise EntityError('Valor não pode ser decimal para este campo')

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
            raise EntityError('Opções devem ser uma lista não vazia de strings')
        self.options = options

        if value is not None and (not isinstance(value, str) or value not in options):
            raise EntityError(f"Valor '{value}' não está entre as opções permitidas: {options}")
        self.value = value

    def _validate_value(self, value):
        if value is not None and (not isinstance(value, str) or value not in self.options):
            raise EntityError(f"Valor '{value}' não está entre as opções permitidas: {self.options}")

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
            raise EntityError('Opções devem ser uma lista não vazia de strings')
        self.options = options

        if max_length is not None and not isinstance(max_length, int):
            raise EntityError('Comprimento máximo deve ser um número inteiro')
        self.max_length = max_length

        if value is not None and not isinstance(value, str):
            raise EntityError('Valor do campo deve ser uma string')
        self.value = value

    def _validate_value(self, value):
        if value is not None and not isinstance(value, str):
            raise EntityError('Valor do campo deve ser uma string')

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
            raise EntityError('Opções devem ser uma lista não vazia de strings')
        self.options = options

        if value is not None and (not isinstance(value, str) or value not in options):
            raise EntityError(f"Valor '{value}' não está entre as opções permitidas: {options}")
        self.value = value

    def _validate_value(self, value):
        if value is not None and (not isinstance(value, str) or value not in self.options):
            raise EntityError(f"Valor '{value}' não está entre as opções permitidas: {self.options}")

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
            raise EntityError('Data mínima deve ser um timestamp inteiro')
        self.min_date = min_date

        if max_date is not None and not isinstance(max_date, int):
            raise EntityError('Data máxima deve ser um timestamp inteiro')
        self.max_date = max_date

        if value is not None:
            if not isinstance(value, int):
                raise EntityError('Data deve ser um timestamp inteiro')
            if min_date is not None and value < min_date:
                raise EntityError(f'Data {value} é anterior à data mínima permitida ({min_date})')
            if max_date is not None and value > max_date:
                raise EntityError(f'Data {value} é posterior à data máxima permitida ({max_date})')
        self.value = value

    def normalize_value(self, value):
        if value is None:
            return None
        try:
            normalized_value = int(value)
        except (TypeError, ValueError):
            raise EntityError('Data deve ser um timestamp inteiro')
        self._validate_value(normalized_value)
        return normalized_value

    def _validate_value(self, value):
        if value is not None:
            if not isinstance(value, int):
                raise EntityError('Data deve ser um timestamp inteiro')
            if self.min_date is not None and value < self.min_date:
                raise EntityError(f'Data {value} é anterior à data mínima permitida ({self.min_date})')
            if self.max_date is not None and value > self.max_date:
                raise EntityError(f'Data {value} é posterior à data máxima permitida ({self.max_date})')

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
            raise EntityError('Valor do checkbox deve ser verdadeiro ou falso')
        self.value = value

    def normalize_value(self, value):
        return bool(value) if value is not None else None

    def _validate_value(self, value):
        if value is not None and not isinstance(value, bool):
            raise EntityError('Valor do checkbox deve ser verdadeiro ou falso')

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
            raise EntityError('Opções devem ser uma lista não vazia de strings')
        self.options = options

        if check_limit is not None:
            if not isinstance(check_limit, int):
                raise EntityError('Limite de seleção deve ser um número inteiro')
            if check_limit > len(options):
                raise EntityError(f'Limite de seleção ({check_limit}) não pode ser maior que o número de opções ({len(options)})')
        self.check_limit = check_limit

        if value is not None:
            if not isinstance(value, list) or len(value) != len(options) or not all(isinstance(val, bool) for val in value):
                raise EntityError(f'Valor deve ser uma lista de booleanos com exatamente {len(options)} elemento(s)')
            if check_limit is not None and sum(value) > check_limit:
                raise EntityError(f'Número de opções selecionadas excede o limite de {check_limit}')
        self.value = value

    def normalize_value(self, value):
        normalized_value = None
        if value is not None:
            if isinstance(value, dict):
                unknown_keys = [key for key in value.keys() if key not in self.options]
                if unknown_keys:
                    raise EntityError(f"Chaves desconhecidas no valor do checkbox: {unknown_keys}")
                normalized_value = []
                for option in self.options:
                    entry = value.get(option)
                    if entry is None:
                        entry = False
                    if isinstance(entry, (int, float)) and entry in (0, 1):
                        entry = bool(entry)
                    if not isinstance(entry, bool):
                        raise EntityError(f"Valor da opção '{option}' deve ser verdadeiro ou falso")
                    normalized_value.append(entry)
            elif isinstance(value, list):
                normalized_value = []
                for entry in value:
                    if entry is None:
                        normalized_value.append(False)
                    elif isinstance(entry, (int, float)) and entry in (0, 1):
                        normalized_value.append(bool(entry))
                    elif isinstance(entry, bool):
                        normalized_value.append(entry)
                    else:
                        raise EntityError(f"Cada entrada do checkbox deve ser verdadeiro ou falso, recebido: {entry}")
            else:
                raise EntityError("Valor do checkbox deve ser um objeto ou lista de booleanos")
        self._validate_value(normalized_value)
        return normalized_value

    def _validate_value(self, value):
        if value is not None:
            if not isinstance(value, list) or len(value) != len(self.options) or not all(isinstance(val, bool) for val in value):
                raise EntityError(f'Valor deve ser uma lista de booleanos com exatamente {len(self.options)} elemento(s)')
            if self.check_limit is not None and sum(value) > self.check_limit:
                raise EntityError(f'Número de opções selecionadas excede o limite de {self.check_limit}')

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
            raise EntityError('Valor do switch deve ser verdadeiro ou falso')
        self.value = value

    def normalize_value(self, value):
        return bool(value) if value is not None else None

    def _validate_value(self, value):
        if value is not None and not isinstance(value, bool):
            raise EntityError('Valor do switch deve ser verdadeiro ou falso')

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
            raise EntityError('Tipo de arquivo inválido')
        self.file_type = file_type

        if min_quantity is not None and not isinstance(min_quantity, int):
            raise EntityError('Quantidade mínima de arquivos deve ser um número inteiro')
        self.min_quantity = min_quantity

        if max_quantity is not None and not isinstance(max_quantity, int):
            raise EntityError('Quantidade máxima de arquivos deve ser um número inteiro')
        self.max_quantity = max_quantity

        if self.min_quantity is not None and self.max_quantity is not None and self.min_quantity > self.max_quantity:
            raise EntityError(f'Quantidade mínima ({min_quantity}) não pode ser maior que a máxima ({max_quantity})')

        if value is not None:
            if isinstance(value, list):
                if not all(isinstance(item, (str, dict)) for item in value):
                    raise EntityError('Cada arquivo deve ser identificado por uma string ou objeto')
                if self.min_quantity is not None and len(value) < self.min_quantity:
                    raise EntityError(f'Número de arquivos ({len(value)}) é menor que o mínimo exigido ({self.min_quantity})')
                if self.max_quantity is not None and len(value) > self.max_quantity:
                    raise EntityError(f'Número de arquivos ({len(value)}) excede o máximo permitido ({self.max_quantity})')
            elif not isinstance(value, (str, dict)):
                raise EntityError('Valor do campo de arquivo deve ser uma string, objeto ou lista')
        self.value = value

    def _validate_value(self, value):
        if value is not None:
            if isinstance(value, list):
                if not all(isinstance(item, (str, dict)) for item in value):
                    raise EntityError('Cada arquivo deve ser identificado por uma string ou objeto')
                if self.min_quantity is not None and len(value) < self.min_quantity:
                    raise EntityError(f'Número de arquivos ({len(value)}) é menor que o mínimo exigido ({self.min_quantity})')
                if self.max_quantity is not None and len(value) > self.max_quantity:
                    raise EntityError(f'Número de arquivos ({len(value)}) excede o máximo permitido ({self.max_quantity})')
            elif not isinstance(value, (str, dict)):
                raise EntityError('Valor do campo de arquivo deve ser uma string, objeto ou lista')

    def to_legacy_dict(self) -> dict:
        base = super().to_legacy_dict()
        base.update({
            "file_type": self.file_type.name,
            "min_quantity": self.min_quantity,
            "max_quantity": self.max_quantity,
            "value": self.value
        })
        return base
