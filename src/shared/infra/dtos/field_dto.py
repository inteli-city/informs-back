from enum import Enum
from typing import Dict, Any, Union

from src.shared.domain.entities.field import CheckBoxGroupField, CheckboxField, DateField, DropDownField, Field, FileField, NumberField, RadioGroupField, SwitchButtonField, TextField, TypeAheadField
from src.shared.domain.enums.fields_enum import FIELD_TYPE
from src.shared.domain.enums.file_type_enum import FILE_TYPE
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError

class FieldDTO:
    field: Field
    _FIELD_BUILDERS = {}

    def __init__(self, field: Field):
        self.field = field
    
    @staticmethod
    def from_dynamo(field_dict: dict):
        if field_dict.get('field_type') is None:
            raise MissingParameters('field_type')
        
        if field_dict.get('field_type') not in [field.value for field in FIELD_TYPE]:
            raise EntityError(f"Tipo de campo '{field_dict.get('field_type')}' inválido")
        
        if field_dict.get('label') is None and field_dict.get('placeholder') is not None:
            field_dict['label'] = field_dict.get('placeholder')
        
        for base_param in ['label', 'required', 'key']:
            if field_dict.get(base_param) is None:
                raise MissingParameters(base_param)
        
        if field_dict.get('order') is None:
            field_dict['order'] = 0

        field_type = FIELD_TYPE[field_dict.get('field_type')]
        base_args = {
            "label": field_dict.get("label"),
            "required": bool(field_dict.get("required")),
            "key": field_dict.get("key"),
            "order": int(field_dict.get("order")),
            "help_text": field_dict.get("help_text"),
        }

        spec = FieldDTO._FIELD_BUILDERS.get(field_type)
        if spec is None:
            raise EntityError(f"Tipo de campo '{field_type}' não suportado")

        required_fields, builder = spec
        FieldDTO._ensure_required(field_dict, required_fields)
        field = builder(base_args, field_dict)
        
        return FieldDTO(field)    

    def to_dynamo(self) -> dict:
        def _serialize_value(value):
            if isinstance(value, Enum):
                return value.name
            if isinstance(value, list):
                return [_serialize_value(item) for item in value]
            if isinstance(value, dict):
                return {key: _serialize_value(val) for key, val in value.items()}
            return value

        base = {
            "field_type": self.field.field_type.name,
            "label": self.field.label,
            "placeholder": self.field.placeholder,
            "required": self.field.required,
            "key": self.field.key,
            "order": self.field.order,
            "help_text": self.field.help_text,
        }

        type_specific_fields = {
            FIELD_TYPE.TEXT_FIELD: {"regex", "formatting", "max_length", "value"},
            FIELD_TYPE.NUMBER_FIELD: {"max_value", "min_value", "decimal", "value"},
            FIELD_TYPE.DROPDOWN_FIELD: {"options", "value"},
            FIELD_TYPE.TYPEAHEAD_FIELD: {"options", "max_length", "value"},
            FIELD_TYPE.RADIO_GROUP_FIELD: {"options", "value"},
            FIELD_TYPE.DATE_FIELD: {"min_date", "max_date", "value"},
            FIELD_TYPE.CHECKBOX_FIELD: {"value"},
            FIELD_TYPE.CHECKBOX_GROUP_FIELD: {"options", "check_limit", "value"},
            FIELD_TYPE.SWITCH_BUTTON_FIELD: {"value"},
            FIELD_TYPE.FILE_FIELD: {"file_type", "min_quantity", "max_quantity", "value"},
        }

        field_type = self.field.field_type
        allowed_fields = type_specific_fields.get(field_type)
        if allowed_fields is None:
            allowed_fields = {
                key for key in vars(self.field).keys()
                if key not in base and key not in {"label", "placeholder"}
            }

        for key in allowed_fields:
            base[key] = _serialize_value(getattr(self.field, key, None))

        return base

    def to_entity(self) -> Field:
        return self.field

    @staticmethod
    def _ensure_required(field_dict: dict, required_fields: set) -> None:
        for field in required_fields:
            if field_dict.get(field) is None:
                raise MissingParameters(field)

    @staticmethod
    def _to_int(value):
        return int(value) if value is not None else None

    @staticmethod
    def _to_float(value):
        return float(value) if value is not None else None

    @staticmethod
    def _build_text_field(base_args: dict, field_dict: dict) -> TextField:
        return TextField(
            **base_args,
            regex=field_dict.get("regex"),
            formatting=field_dict.get("formatting"),
            max_length=FieldDTO._to_int(field_dict.get("max_length")),
            value=field_dict.get("value"),
        )

    @staticmethod
    def _build_number_field(base_args: dict, field_dict: dict) -> NumberField:
        return NumberField(
            **base_args,
            decimal=bool(field_dict.get("decimal")),
            max_value=FieldDTO._to_float(field_dict.get("max_value")),
            min_value=FieldDTO._to_float(field_dict.get("min_value")),
            value=FieldDTO._to_float(field_dict.get("value")),
        )

    @staticmethod
    def _build_dropdown_field(base_args: dict, field_dict: dict) -> DropDownField:
        return DropDownField(
            **base_args,
            options=field_dict.get("options"),
            value=field_dict.get("value"),
        )

    @staticmethod
    def _build_typeahead_field(base_args: dict, field_dict: dict) -> TypeAheadField:
        return TypeAheadField(
            **base_args,
            options=field_dict.get("options"),
            max_length=FieldDTO._to_int(field_dict.get("max_length")),
            value=field_dict.get("value"),
        )

    @staticmethod
    def _build_radio_group_field(base_args: dict, field_dict: dict) -> RadioGroupField:
        return RadioGroupField(
            **base_args,
            options=field_dict.get("options"),
            value=field_dict.get("value"),
        )

    @staticmethod
    def _build_date_field(base_args: dict, field_dict: dict) -> DateField:
        return DateField(
            **base_args,
            min_date=FieldDTO._to_int(field_dict.get("min_date")),
            max_date=FieldDTO._to_int(field_dict.get("max_date")),
            value=FieldDTO._to_int(field_dict.get("value")),
        )

    @staticmethod
    def _build_checkbox_field(base_args: dict, field_dict: dict) -> CheckboxField:
        checkbox_value = field_dict.get("value")
        return CheckboxField(
            **base_args,
            value=bool(checkbox_value) if checkbox_value is not None else None,
        )

    @staticmethod
    def _build_checkbox_group_field(base_args: dict, field_dict: dict) -> CheckBoxGroupField:
        value_raw = field_dict.get("value")
        options = field_dict.get("options")
        normalized_value = None

        if value_raw is not None:
            if isinstance(value_raw, dict):
                if not isinstance(options, list) or not options:
                    raise EntityError("Opções são obrigatórias para o tipo CheckboxGroup")
                unknown_keys = [key for key in value_raw.keys() if key not in options]
                if unknown_keys:
                    raise EntityError(f"Chaves desconhecidas no valor do checkbox: {unknown_keys}")
                normalized_value = []
                for option in options:
                    entry = value_raw.get(option)
                    if entry is None:
                        entry = False
                    if isinstance(entry, (int, float)) and entry in (0, 1):
                        entry = bool(entry)
                    if not isinstance(entry, bool):
                        raise EntityError(f"Valor da opção '{option}' deve ser verdadeiro ou falso")
                    normalized_value.append(entry)
            elif isinstance(value_raw, list):
                normalized_value = []
                for entry in value_raw:
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

        return CheckBoxGroupField(
            **base_args,
            options=options,
            check_limit=FieldDTO._to_int(field_dict.get("check_limit")),
            value=normalized_value,
        )

    @staticmethod
    def _build_switch_button_field(base_args: dict, field_dict: dict) -> SwitchButtonField:
        switch_value = field_dict.get("value")
        return SwitchButtonField(
            **base_args,
            value=bool(switch_value) if switch_value is not None else None,
        )

    @staticmethod
    def _build_file_field(base_args: dict, field_dict: dict) -> FileField:
        file_type = field_dict.get("file_type")
        if file_type not in [file_type.value for file_type in FILE_TYPE]:
            raise EntityError(f"Tipo de arquivo '{file_type}' inválido")
        return FileField(
            **base_args,
            file_type=FILE_TYPE[file_type],
            min_quantity=FieldDTO._to_int(field_dict.get("min_quantity")),
            max_quantity=FieldDTO._to_int(field_dict.get("max_quantity")),
            value=field_dict.get("value"),
        )


FieldDTO._FIELD_BUILDERS = {
    FIELD_TYPE.TEXT_FIELD: (set(), FieldDTO._build_text_field),
    FIELD_TYPE.NUMBER_FIELD: ({"decimal"}, FieldDTO._build_number_field),
    FIELD_TYPE.DROPDOWN_FIELD: ({"options"}, FieldDTO._build_dropdown_field),
    FIELD_TYPE.TYPEAHEAD_FIELD: ({"options"}, FieldDTO._build_typeahead_field),
    FIELD_TYPE.RADIO_GROUP_FIELD: ({"options"}, FieldDTO._build_radio_group_field),
    FIELD_TYPE.DATE_FIELD: (set(), FieldDTO._build_date_field),
    FIELD_TYPE.CHECKBOX_FIELD: (set(), FieldDTO._build_checkbox_field),
    FIELD_TYPE.CHECKBOX_GROUP_FIELD: ({"options"}, FieldDTO._build_checkbox_group_field),
    FIELD_TYPE.SWITCH_BUTTON_FIELD: (set(), FieldDTO._build_switch_button_field),
    FIELD_TYPE.FILE_FIELD: ({"file_type", "min_quantity", "max_quantity"}, FieldDTO._build_file_field),
}
