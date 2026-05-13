"""
Builders compartilhados para serializar entidades de Form e seus filhos
(Section, Field, Justification, InformationField) em dicts prontos para
ResponseSchema.

Antes desta extração, `create_form_viewmodel.py` e `get_all_forms_viewmodel.py`
tinham classes praticamente idênticas (FieldViewmodel, SectionViewmodel,
JustificationViewmodel, etc.), com algumas variações pequenas controladas
por flags. SonarCloud reportava ~64% de duplicação nos dois arquivos.

Aqui as variações ficam explícitas em parâmetros nomeados:
- `include_dynamic_extras`: inclui campos opcionais como min_date/max_date/value
  (úteis para responses de listagem/leitura, dispensáveis em response de
  criação onde o form ainda não foi preenchido).
- `expand_selected`: serializa `Justification.selected.__dict__` em vez de
  retornar `null` (útil para forms já submetidos).
"""

from enum import Enum
from typing import Any, Dict

from src.shared.domain.entities.field import Field
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import InformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.fields_enum import FIELD_TYPE


def build_field_dict(field: Field, *, include_dynamic_extras: bool = False) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "field_type": field.field_type.value,
        "label": field.label,
        "required": field.required,
        "key": field.key,
        "order": field.order,
        "help_text": getattr(field, "help_text", None),
    }

    if field.field_type == FIELD_TYPE.TEXT_FIELD:
        base["regex"] = getattr(field, "regex", None)
        base["max_length"] = getattr(field, "max_length", None)

    if hasattr(field, "options"):
        base["options"] = field.options
    if hasattr(field, "max_value"):
        base["max_value"] = field.max_value
    if hasattr(field, "min_value"):
        base["min_value"] = field.min_value
    if hasattr(field, "decimal"):
        base["decimal"] = field.decimal
    if hasattr(field, "check_limit"):
        base["check_limit"] = field.check_limit
    if hasattr(field, "file_type"):
        base["file_type"] = getattr(field.file_type, "value", None)
        base["min_quantity"] = getattr(field, "min_quantity", None)
        base["max_quantity"] = getattr(field, "max_quantity", None)

    if include_dynamic_extras:
        if hasattr(field, "min_date"):
            base["min_date"] = field.min_date
        if hasattr(field, "max_date"):
            base["max_date"] = field.max_date
        if hasattr(field, "value"):
            value = field.value
            base["value"] = value.value if isinstance(value, Enum) else value

    return base


def build_section_dict(section: Section, *, include_dynamic_extras: bool = False) -> Dict[str, Any]:
    return {
        "section_id": section.section_id,
        "fields": [
            build_field_dict(field, include_dynamic_extras=include_dynamic_extras)
            for field in section.fields
        ],
    }


def build_justification_option_dict(option: JustificationOption) -> Dict[str, Any]:
    return {
        "option": option.option,
        "required_image": option.required_image,
        "required_text": option.required_text,
    }


def build_justification_dict(
    justification: Justification, *, expand_selected: bool = False
) -> Dict[str, Any]:
    selected = justification.selected
    return {
        "options": [build_justification_option_dict(opt) for opt in justification.options],
        "selected": selected.__dict__ if (expand_selected and selected) else None,
    }


def build_information_field_dict(information_field: InformationField) -> Dict[str, Any]:
    return {
        attr: (
            getattr(information_field, attr).value
            if isinstance(getattr(information_field, attr), Enum)
            else getattr(information_field, attr)
        )
        for attr in vars(information_field)
    }


def build_form_dict(
    form: Form,
    *,
    include_dynamic_extras: bool = False,
    expand_selected: bool = False,
) -> Dict[str, Any]:
    return {
        "id": form.id,
        "status": form.status.value,
        "form_title": form.form_title,
        "user_id": form.user_id,
        "area": form.area,
        "system": form.system,
        "city": form.city,
        "street": form.street,
        "latitude": form.latitude,
        "longitude": form.longitude,
        "priority": int(form.priority.value),
        "observation": form.observation,
        "expiration_date": form.expiration_date,
        "justification": build_justification_dict(
            form.justification, expand_selected=expand_selected
        ),
        "sections": [
            build_section_dict(section, include_dynamic_extras=include_dynamic_extras)
            for section in form.sections
        ],
        "in_progress_at": form.in_progress_at,
        "cancelled_at": form.cancelled_at,
        "completed_at": form.completed_at,
        "created_by": form.created_by,
        "created_at": form.created_at,
        "updated_at": form.updated_at,
        "information_fields": (
            [build_information_field_dict(info) for info in form.information_fields]
            if form.information_fields
            else None
        ),
        "number": form.number,
    }
