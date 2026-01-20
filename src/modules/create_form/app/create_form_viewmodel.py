from enum import Enum
from typing import List, Optional
from src.shared.domain.entities.field import Field
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.image_upload import ImageUpload
from src.shared.domain.entities.information_field import InformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.fields_enum import FIELD_TYPE


class FieldViewmodel:
    def __init__(self, field: Field):
        self.field = field
    
    def to_dict(self):
        base = {
            'field_type': self.field.field_type.value,
            'label': self.field.label,
            'required': self.field.required,
            'key': self.field.key,
            'order': self.field.order,
            'help_text': getattr(self.field, 'help_text', None)
        }

        if self.field.field_type == FIELD_TYPE.TEXT_FIELD:
            base.update({
                'regex': getattr(self.field, 'regex', None),
                'max_length': getattr(self.field, 'max_length', None)
            })
        if hasattr(self.field, 'options'):
            base['options'] = getattr(self.field, 'options')
        if hasattr(self.field, 'max_value'):
            base['max_value'] = getattr(self.field, 'max_value')
        if hasattr(self.field, 'min_value'):
            base['min_value'] = getattr(self.field, 'min_value')
        if hasattr(self.field, 'decimal'):
            base['decimal'] = getattr(self.field, 'decimal')
        if hasattr(self.field, 'check_limit'):
            base['check_limit'] = getattr(self.field, 'check_limit')
        if hasattr(self.field, 'file_type'):
            base['file_type'] = getattr(self.field.file_type, 'value', None)
            base['min_quantity'] = getattr(self.field, 'min_quantity', None)
            base['max_quantity'] = getattr(self.field, 'max_quantity', None)

        return base


class SectionViewmodel:
    def __init__(self, section: Section):
        self.section = section
    
    def to_dict(self):
        return {
            'section_id': self.section.section_id,
            'fields': [FieldViewmodel(field).to_dict() for field in self.section.fields]
        }


class JustificationOptionViewmodel:
    def __init__(self, justification_option: JustificationOption):
        self.justification_option = justification_option

    def to_dict(self):
        return {
            'option': self.justification_option.option,
            'required_image': self.justification_option.required_image,
            'required_text': self.justification_option.required_text
        }


class JustificationViewmodel:
    def __init__(self, justification: Justification):
        self.justification = justification

    def to_dict(self):
        return {
            'options': [JustificationOptionViewmodel(option).to_dict() for option in self.justification.options],
            'selected': None
        }


class InformationFieldViewmodel:
    def __init__(self, information_field: InformationField):
        self.information_field = information_field

    def to_dict(self):
        return {
            attr: (
                getattr(self.information_field, attr).value
                if isinstance(getattr(self.information_field, attr), Enum)
                else getattr(self.information_field, attr)
            )
            for attr in vars(self.information_field)
        }


class FormViewmodel:
    def __init__(self, form: Form):
        self.form = form

    def to_dict(self):
        return {
            'id': self.form.id,
            'status': self.form.status.value,
            'form_title': self.form.form_title,
            'user_id': self.form.user_id,
            'system': self.form.system,
            'city': self.form.city,
            'street': self.form.street,
            'latitude': self.form.latitude,
            'longitude': self.form.longitude,
            'priority': int(self.form.priority.value),
            'observation': self.form.observation,
            'expiration_date': self.form.expiration_date,
            'justification': JustificationViewmodel(self.form.justification).to_dict(),
            'sessions': [SectionViewmodel(section).to_dict() for section in self.form.sections],
            'in_progress_at': self.form.in_progress_at,
            'cancelled_at': self.form.cancelled_at,
            'completed_at': self.form.completed_at,
            'created_by': self.form.created_by,
            'created_at': self.form.created_at,
            'updated_at': self.form.updated_at,
            'information_fields': [InformationFieldViewmodel(information_field).to_dict() for information_field in self.form.information_fields] if self.form.information_fields else None,
            'number': self.form.number
        }
    

class CreateFormViewmodel:
    def __init__(self, form: Form, images: Optional[List[ImageUpload]] = None):
        self.form = form
        self.images = images or []
    
    def to_dict(self):
        payload = FormViewmodel(self.form).to_dict()
        payload["images"] = [
            image.to_dict() if isinstance(image, ImageUpload) else image
            for image in self.images
        ]
        return payload
