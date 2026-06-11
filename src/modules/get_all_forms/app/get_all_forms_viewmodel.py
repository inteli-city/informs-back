from typing import List, Optional

from src.shared.domain.entities.field import Field
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import InformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.helpers.contracts.endpoints.get_all_forms_contract import GetAllFormsResponseSchema
from src.shared.helpers.viewmodels.form_dict_builders import (
    build_field_dict,
    build_form_dict,
    build_information_field_dict,
    build_justification_dict,
    build_justification_option_dict,
    build_section_dict,
)


# Wrappers finos sobre src.shared.helpers.viewmodels.form_dict_builders.
# Mantemos as classes públicas para retro-compat com os testes que importam
# FieldViewmodel/SectionViewmodel/etc diretamente.


class FieldViewmodel:
    def __init__(self, field: Field):
        self.field = field

    def to_dict(self):
        # Listagem de forms já existentes: incluímos value/min_date/max_date
        # quando aplicável (o form pode estar preenchido).
        return build_field_dict(self.field, include_dynamic_extras=True)


class SectionViewmodel:
    def __init__(self, section: Section):
        self.section = section

    def to_dict(self):
        return build_section_dict(self.section, include_dynamic_extras=True)


class JustificationOptionViewmodel:
    def __init__(self, justification_option: JustificationOption):
        self.justification_option = justification_option

    def to_dict(self):
        return build_justification_option_dict(self.justification_option)


class JustificationViewmodel:
    def __init__(self, justification: Justification):
        self.justification = justification

    def to_dict(self):
        # Quando há `selected`, expandimos seus campos para que o cliente
        # tenha a justificativa real (não apenas a lista de opções).
        return build_justification_dict(self.justification, expand_selected=True)


class InformationFieldViewmodel:
    def __init__(self, information_field: InformationField):
        self.information_field = information_field

    def to_dict(self):
        return build_information_field_dict(self.information_field)


class FormItemViewmodel:
    def __init__(self, form: Form):
        self.form = form

    def to_dict(self):
        return build_form_dict(
            self.form, include_dynamic_extras=True, expand_selected=True
        )


class GetAllFormsViewmodel:
    def __init__(self, forms: List[Form], limit: Optional[int], last_evaluated_key: Optional[str]):
        self.forms = forms
        self.limit = limit
        self.last_evaluated_key = last_evaluated_key

    def to_dict(self):
        payload = {
            "forms": [FormItemViewmodel(form).to_dict() for form in self.forms],
            "limit": self.limit,
            "last_evaluated_key": self.last_evaluated_key,
        }
        return GetAllFormsResponseSchema.model_validate(payload).model_dump()
