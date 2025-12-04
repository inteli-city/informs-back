from enum import Enum
from typing import List, Optional

from src.shared.domain.entities.field import Field
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY


class FieldViewmodel:
    def __init__(self, field: Field):
        self.field = field

    def to_dict(self):
        return {attr: getattr(self.field, attr).value if isinstance(getattr(self.field, attr), Enum) else getattr(self.field, attr) for attr in vars(self.field)}


class SectionViewmodel:
    def __init__(self, section: Section):
        self.section_id = section.section_id
        self.fields = section.fields

    def to_dict(self):
        return {
            "section_id": self.section_id,
            "fields": [FieldViewmodel(field).to_dict() for field in self.fields],
        }


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

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status.value if isinstance(self.status, FORM_STATUS) else self.status,
            "form_title": self.form_title,
            "user_id": self.user_id,
            "system": self.system,
            "city": self.city,
            "street": self.street,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "priority": self.priority.value if isinstance(self.priority, PRIORITY) else self.priority,
            "observation": self.observation,
            "expiration_date": self.expiration_date,
            "justification": JustificationViewmodel(self.justification).to_dict(),
            "sessions": [SectionViewmodel(section).to_dict() for section in self.sections],
            "in_progress_at": self.in_progress_at,
            "cancelled_at": self.cancelled_at,
            "completed_at": self.completed_at,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
