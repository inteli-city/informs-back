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


class RemovedFormMarkerViewmodel:
    """Marcador de OS que saiu do pool numa consulta incremental: só id, status, posse, instante e a marca."""

    def __init__(self, form: Form):
        self.form = form

    def to_dict(self):
        return {
            "id": self.form.id,
            "status": self.form.status.value,
            "possession": self.form.possession.value,
            "updated_at": self.form.updated_at,
            "removed_from_pool": True,
        }


class GetAllFormsViewmodel:
    def __init__(
        self,
        forms: List[Form],
        limit: Optional[int],
        last_evaluated_key: Optional[str],
        server_time: Optional[int] = None,
        in_pool: Optional[List[bool]] = None,
    ):
        self.forms = forms
        self.limit = limit
        self.last_evaluated_key = last_evaluated_key
        # `server_time` vem da controller em toda resposta. Sem ele (chamada que não o informa), o campo sai do
        # corpo em vez de virar `null`. `in_pool` só existe na consulta incremental.
        self.server_time = server_time
        self.in_pool = in_pool

    def _item(self, index: int, form: Form) -> dict:
        if self.in_pool is not None and not self.in_pool[index]:
            return RemovedFormMarkerViewmodel(form).to_dict()
        return FormItemViewmodel(form).to_dict()

    def to_dict(self):
        payload = {
            "forms": [self._item(index, form) for index, form in enumerate(self.forms)],
            "limit": self.limit,
            "last_evaluated_key": self.last_evaluated_key,
        }
        if self.server_time is not None:
            payload["server_time"] = self.server_time
        # Sem `server_time` informado, o campo fica fora do corpo (e não vira `null`).
        excluded = None if self.server_time is not None else {"server_time"}
        return GetAllFormsResponseSchema.model_validate(payload).model_dump(exclude=excluded)
