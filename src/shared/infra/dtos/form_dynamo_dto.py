from decimal import Decimal
from typing import List, Optional

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import InformationField
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.infra.dtos.information_field_dto import InformationFieldDTO
from src.shared.infra.dtos.justification_dto import JustificationDTO
from src.shared.infra.dtos.section_dto import SectionDTO


class FormDynamoDTO:
    form_title: str
    id: str
    user_id: str
    created_by: str
    template: Optional[str]
    system: str
    city: str
    area: Optional[str]
    street: str
    number: Optional[int]
    latitude: float
    longitude: float
    priority: PRIORITY
    observation: Optional[str]
    expiration_date: Optional[int]
    status: FORM_STATUS
    in_progress_at: Optional[int]
    cancelled_at: Optional[int]
    completed_at: Optional[int]
    created_at: int
    updated_at: int
    sections: List[Section]
    justification: Optional[Justification]
    information_fields: Optional[List[InformationField]]

    def __init__(self, form_title: str, id: str, user_id: str, created_by: str, system: str, city: str, street: str, latitude: float, longitude: float, priority: PRIORITY, status: FORM_STATUS, created_at: int, updated_at: int, sections: List[Section], template: Optional[str] = None, area: Optional[str] = None, number: Optional[int] = None, observation: Optional[str] = None, expiration_date: Optional[int] = None, in_progress_at: Optional[int] = None, cancelled_at: Optional[int] = None, completed_at: Optional[int] = None, justification: Optional[Justification] = None, information_fields: Optional[List[InformationField]] = None):
        self.form_title = form_title
        self.id = id
        self.user_id = user_id
        self.created_by = created_by
        self.template = template
        self.area = area
        self.system = system
        self.street = street
        self.city = city
        self.number = number
        self.latitude = latitude
        self.longitude = longitude
        self.priority = priority
        self.observation = observation
        self.expiration_date = expiration_date
        self.status = status
        self.in_progress_at = in_progress_at
        self.cancelled_at = cancelled_at
        self.completed_at = completed_at
        self.created_at = created_at
        self.updated_at = updated_at
        self.justification = justification
        self.sections = sections
        self.information_fields = information_fields


    @staticmethod
    def from_entity(form: Form) -> "FormDynamoDTO":
        return FormDynamoDTO(
            form_title=form.form_title,
            id=form.id,
            user_id=form.user_id,
            created_by=form.created_by,
            template=form.template,
            area=form.area,
            system=form.system,
            street=form.street,
            city=form.city,
            number=form.number,
            latitude=form.latitude,
            longitude=form.longitude,
            priority=form.priority,
            observation=form.observation,
            expiration_date=form.expiration_date,
            status=form.status,
            in_progress_at=form.in_progress_at,
            cancelled_at=form.cancelled_at,
            completed_at=form.completed_at,
            created_at=form.created_at,
            updated_at=form.updated_at,
            justification=form.justification,
            sections=form.sections,
            information_fields=form.information_fields
        )

    def to_dynamo(self) -> dict:
        return {
            'form_title': self.form_title,
            'id': self.id,
            'user_id': self.user_id,
            'created_by': self.created_by,
            'template': self.template,
            'area': self.area,
            'system': self.system,
            'street': self.street,
            'city': self.city,
            'number': self.number,
            'latitude': Decimal(str(self.latitude)),
            'longitude': Decimal(str(self.longitude)),
            'priority': self.priority.value,
            'observation': self.observation,
            'expiration_date': self.expiration_date,
            'status': self.status.value,
            'in_progress_at': self.in_progress_at,
            'cancelled_at': self.cancelled_at,
            'completed_at': self.completed_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'justification': JustificationDTO.from_entity(self.justification).to_dynamo() if self.justification else None,
            'sections': [
                SectionDTO.from_entity(section).to_dynamo() for section in self.sections
            ],
            'information_fields': [InformationFieldDTO.from_entity(information_field).to_dynamo() for information_field in self.information_fields] if self.information_fields else None
        }
    
    @staticmethod
    def from_dynamo(data: dict) -> "FormDynamoDTO":
        return FormDynamoDTO(
            form_title=data['form_title'],
            id=data['id'],
            user_id=data['user_id'],
            created_by=data['created_by'],
            template=data.get('template'),
            area=data.get('area'),
            system=data['system'],
            street=data['street'],
            city=data['city'],
            number=int(data['number']) if data.get('number') is not None else None,
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            priority=PRIORITY(data['priority']),
            observation=data.get('observation'),
            expiration_date=int(data['expiration_date']) if data.get('expiration_date') is not None else None,
            status=FORM_STATUS(data['status']),
            in_progress_at=int(data['in_progress_at']) if data.get('in_progress_at') is not None else None,
            cancelled_at=int(data['cancelled_at']) if data.get('cancelled_at') is not None else None,
            completed_at=int(data['completed_at']) if data.get('completed_at') is not None else None,
            created_at=int(data['created_at']),
            updated_at=int(data['updated_at']),
            justification=JustificationDTO.from_dynamo(data['justification']).to_entity() if data.get('justification') else None,
            sections=[SectionDTO.from_dynamo(section).to_entity() for section in data['sections']],
            information_fields=[InformationFieldDTO.from_dynamo(information_field).to_entity() for information_field in data['information_fields']] if data.get('information_fields') else None
        )
    
    def to_entity(self) -> Form:
        return Form(
            id=self.id,
            form_title=self.form_title,
            user_id=self.user_id,
            created_by=self.created_by,
            template=self.template,
            area=self.area,
            system=self.system,
            street=self.street,
            city=self.city,
            number=self.number,
            latitude=self.latitude,
            longitude=self.longitude,
            priority=self.priority,
            observation=self.observation,
            expiration_date=self.expiration_date,
            status=self.status,
            in_progress_at=self.in_progress_at,
            cancelled_at=self.cancelled_at,
            completed_at=self.completed_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            justification=self.justification,
            sections=self.sections,
            information_fields=self.information_fields
        )
