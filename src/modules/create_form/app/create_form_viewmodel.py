from typing import List, Optional

from src.shared.domain.entities.field import Field
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.file_upload import FileUpload
from src.shared.domain.entities.information_field import InformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.helpers.contracts.endpoints.create_form_contract import CreateFormResponseSchema
from src.shared.helpers.viewmodels.form_dict_builders import (
    build_field_dict,
    build_form_dict,
    build_information_field_dict,
    build_justification_dict,
    build_justification_option_dict,
    build_section_dict,
)


# As classes abaixo continuam exportadas como antes (testes importam direto).
# A lógica vive em src.shared.helpers.viewmodels.form_dict_builders e é
# compartilhada com get_all_forms_viewmodel — antes ambos duplicavam ~92
# linhas idênticas (~64% de duplicação detectada pelo SonarCloud).


class FieldViewmodel:
    def __init__(self, field: Field):
        self.field = field

    def to_dict(self):
        # Resposta de criação: ainda não há valores preenchidos, então
        # ignoramos os "extras dinâmicos" (min_date, max_date, value).
        return build_field_dict(self.field, include_dynamic_extras=False)


class SectionViewmodel:
    def __init__(self, section: Section):
        self.section = section

    def to_dict(self):
        return build_section_dict(self.section, include_dynamic_extras=False)


class JustificationOptionViewmodel:
    def __init__(self, justification_option: JustificationOption):
        self.justification_option = justification_option

    def to_dict(self):
        return build_justification_option_dict(self.justification_option)


class JustificationViewmodel:
    def __init__(self, justification: Justification):
        self.justification = justification

    def to_dict(self):
        # Form recém-criado nunca tem `selected`, então não expandimos.
        return build_justification_dict(self.justification, expand_selected=False)


class InformationFieldViewmodel:
    def __init__(self, information_field: InformationField):
        self.information_field = information_field

    def to_dict(self):
        return build_information_field_dict(self.information_field)


class FormViewmodel:
    def __init__(self, form: Form):
        self.form = form

    def to_dict(self):
        return build_form_dict(
            self.form, include_dynamic_extras=False, expand_selected=False
        )


class CreateFormViewmodel:
    def __init__(self, form: Form, files: Optional[List[FileUpload]] = None):
        self.form = form
        self.files = files or []

    def to_dict(self):
        payload = FormViewmodel(self.form).to_dict()
        payload["files"] = [
            file.to_dict() if isinstance(file, FileUpload) else file
            for file in self.files
        ]
        return CreateFormResponseSchema.model_validate(payload).model_dump()
