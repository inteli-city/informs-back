from typing import Optional

from src.modules.get_template_forms.app.get_template_forms_usecase import TemplateFormsPage
from src.shared.domain.entities.template_form_summary import TemplateFormSummary
from src.shared.helpers.contracts.endpoints.template_versioning_contract import GetTemplateFormsResponseSchema


def build_template_form_summary_dict(form: TemplateFormSummary) -> dict:
    return {
        "id": form.id,
        "form_title": form.form_title,
        "system": form.system,
        "status": form.status.value,
        "possession": form.possession.value,
        "created_at": form.created_at,
        "template_version": form.template_version,
        "user_id": form.user_id,
        "street": form.street,
        "number": form.number,
        "city": form.city,
    }


class GetTemplateFormsViewmodel:
    def __init__(self, page: TemplateFormsPage, limit: Optional[int]):
        self.page = page
        self.limit = limit

    def to_dict(self):
        payload = {
            "template_id": self.page.template.id,
            "template_version": self.page.template.version,
            "in_use": self.page.in_use,
            "forms": [build_template_form_summary_dict(form) for form in self.page.forms],
            "limit": self.limit,
            "last_evaluated_key": self.page.last_evaluated_key,
        }
        return GetTemplateFormsResponseSchema.model_validate(payload).model_dump()
