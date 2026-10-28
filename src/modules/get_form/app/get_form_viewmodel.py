from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.contracts.endpoints.get_form_contract import GetFormResponseSchema
from src.shared.helpers.viewmodels.form_dict_builders import (
    build_field_vars_dict,
    build_information_field_dict,
    build_section_dict,
)


class JustificationOptionViewmodel:
    def __init__(self, justification_option: JustificationOption):
        self.option = justification_option.option
        self.required_image = justification_option.required_image
        self.required_text = justification_option.required_text

    def to_dict(self):
        return {
            "option": self.option,
            "required_image": self.required_image,
            "required_text": self.required_text,
        }


class SelectedJustificationViewmodel:
    def __init__(self, selected: SelectedJustification):
        self.option = selected.option
        self.text = selected.text
        self.image_url = selected.image_url

    def to_dict(self):
        return {
            "option": self.option,
            "text": self.text,
            "image_url": self.image_url,
        }


class JustificationViewmodel:
    def __init__(self, justification: Justification):
        self.options = [JustificationOptionViewmodel(option).to_dict() for option in justification.options]
        self.selected = SelectedJustificationViewmodel(justification.selected).to_dict() if justification.selected else None
        self.selected_option = justification.selected_option
        self.justification_text = justification.justification_text
        self.justification_image = justification.justification_image

    def to_dict(self):
        return {
            "options": self.options,
            "selected": self.selected,
            "selected_option": self.selected_option,
            "justification_text": self.justification_text,
            "justification_image": self.justification_image,
        }


class GetFormViewmodel:
    def __init__(self, form: Form):
        self.id = form.id
        self.status = form.status
        self.form_title = form.form_title
        self.user_id = form.user_id
        self.area = form.area
        self.system = form.system
        self.city = form.city
        self.street = form.street
        self.latitude = form.latitude
        self.longitude = form.longitude
        self.priority = form.priority
        self.observation = form.observation
        self.expiration_date = form.expiration_date
        self.sections = form.sections
        self.justification = form.justification
        self.in_progress_at = form.in_progress_at
        self.cancelled_at = form.cancelled_at
        self.completed_at = form.completed_at
        self.created_by = form.created_by
        self.created_at = form.created_at
        self.updated_at = form.updated_at
        self.information_fields = form.information_fields
        self.number = form.number
        self.external_id = form.external_id
        self.origin = form.origin
        self.service_type = form.service_type
        self.occurred_at = form.occurred_at
        self.scheduled_start_at = form.scheduled_start_at
        self.scheduled_end_at = form.scheduled_end_at
        self.attributes = form.attributes
        self.completed_by = form.completed_by
        self.possession = form.possession
        self.claimed_at = form.claimed_at
        self.released_at = form.released_at
        self.assignment_source = form.assignment_source
        self.template_version = form.template_version

    def to_dict(self):
        payload = {
            "id": self.id,
            "status": self.status.value if isinstance(self.status, FormStatus) else self.status,
            "form_title": self.form_title,
            "user_id": self.user_id,
            "area": self.area,
            "system": self.system,
            "city": self.city,
            "street": self.street,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "priority": self.priority.value if isinstance(self.priority, Priority) else self.priority,
            "observation": self.observation,
            "expiration_date": self.expiration_date,
            "justification": JustificationViewmodel(self.justification).to_dict(),
            "sections": [
                build_section_dict(section, field_serializer=build_field_vars_dict)
                for section in self.sections
            ],
            "in_progress_at": self.in_progress_at,
            "cancelled_at": self.cancelled_at,
            "completed_at": self.completed_at,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "information_fields": (
                [build_information_field_dict(info) for info in self.information_fields]
                if self.information_fields
                else None
            ),
            "number": self.number,
            "external_id": self.external_id,
            "origin": self.origin.value if self.origin else None,
            "service_type": self.service_type,
            "occurred_at": self.occurred_at,
            "scheduled_start_at": self.scheduled_start_at,
            "scheduled_end_at": self.scheduled_end_at,
            "attributes": self.attributes,
            "completed_by": self.completed_by,
            "possession": self.possession.value,
            "claimed_at": self.claimed_at,
            "released_at": self.released_at,
            "assignment_source": self.assignment_source.value if self.assignment_source else None,
            "template_version": self.template_version,
        }
        validated = GetFormResponseSchema.model_validate(payload).model_dump()
        validated["priority"] = self.priority.value if isinstance(self.priority, Priority) else self.priority
        return validated
