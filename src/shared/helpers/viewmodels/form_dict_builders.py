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
from typing import Any, Callable, Dict, Optional

from src.shared.domain.entities.field import Field
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import InformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.fields_enum import FieldType


# Atributos opcionais que copiamos diretamente quando presentes no field.
_OPTIONAL_PASSTHROUGH_ATTRS = ("options", "max_value", "min_value", "decimal", "check_limit")


def _add_optional_passthrough(base: Dict[str, Any], field: Field) -> None:
    for attr in _OPTIONAL_PASSTHROUGH_ATTRS:
        if hasattr(field, attr):
            base[attr] = getattr(field, attr)


def _add_file_attrs(base: Dict[str, Any], field: Field) -> None:
    if not hasattr(field, "file_type"):
        return
    base["file_type"] = getattr(field.file_type, "value", None)
    base["min_quantity"] = getattr(field, "min_quantity", None)
    base["max_quantity"] = getattr(field, "max_quantity", None)


def _add_dynamic_extras(base: Dict[str, Any], field: Field) -> None:
    if hasattr(field, "min_date"):
        base["min_date"] = field.min_date
    if hasattr(field, "max_date"):
        base["max_date"] = field.max_date
    if hasattr(field, "value"):
        value = field.value
        base["value"] = value.value if isinstance(value, Enum) else value


def build_field_dict(field: Field, *, include_dynamic_extras: bool = False) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "field_type": field.field_type.value,
        "label": field.label,
        "required": field.required,
        "key": field.key,
        "order": field.order,
        "help_text": getattr(field, "help_text", None),
    }

    if field.field_type == FieldType.TEXT_FIELD:
        base["regex"] = getattr(field, "regex", None)
        base["max_length"] = getattr(field, "max_length", None)

    _add_optional_passthrough(base, field)
    _add_file_attrs(base, field)

    if include_dynamic_extras:
        _add_dynamic_extras(base, field)

    return base


def build_field_vars_dict(field: Field) -> Dict[str, Any]:
    """Serialização dinâmica de field: espelha todos os atributos da entidade.

    Diferente de `build_field_dict` (chaves explícitas), este dump inclui
    atributos como `placeholder`/`formatting`/`value` que os endpoints de
    template e `GET /form` sempre expuseram — não trocar um pelo outro sem
    conferir o contrato de resposta.
    """
    return {
        attr: getattr(field, attr).value if isinstance(getattr(field, attr), Enum) else getattr(field, attr)
        for attr in vars(field)
    }


def build_section_dict(
    section: Section,
    *,
    include_dynamic_extras: bool = False,
    field_serializer: Optional[Callable[[Field], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    if field_serializer is None:
        def field_serializer(field: Field) -> Dict[str, Any]:
            return build_field_dict(field, include_dynamic_extras=include_dynamic_extras)
    return {
        "section_id": section.section_id,
        "section_instance": section.section_instance,
        "is_duplicable": section.is_duplicable,
        "fields": [field_serializer(field) for field in section.fields],
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
        "external_id": form.external_id,
        "origin": form.origin.value if form.origin else None,
        "service_type": form.service_type,
        "occurred_at": form.occurred_at,
        "scheduled_start_at": form.scheduled_start_at,
        "scheduled_end_at": form.scheduled_end_at,
        "attributes": form.attributes,
        "completed_by": form.completed_by,
    }
