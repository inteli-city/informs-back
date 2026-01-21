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
    form_id: str
    id: str
    created_by: str
    user_id: str
    template: Optional[str]
    area: Optional[str]
    system: str
    street: str
    city: str
    number: Optional[int]
    latitude: float
    longitude: float
    description: Optional[str]
    observation: Optional[str]
    priority: PRIORITY
    status: FORM_STATUS
    expiration_date: Optional[int]
    created_at: int
    start_date: Optional[int]
    in_progress_at: Optional[int]
    conclusion_date: Optional[int]
    completed_at: Optional[int]
    cancelled_at: Optional[int]
    updated_at: int
    justification: Justification
    sections: List[Section]
    information_fields: Optional[List[InformationField]]

    def __init__(
        self,
        form_title: str,
        user_id: str,
        system: str,
        street: str,
        city: str,
        latitude: float,
        longitude: float,
        priority: PRIORITY,
        status: FORM_STATUS,
        sections: List[Section],
        form_id: Optional[str] = None,
        id: Optional[str] = None,
        created_by: Optional[str] = None,
        template: Optional[str] = None,
        area: Optional[str] = None,
        number: Optional[int] = None,
        description: Optional[str] = None,
        observation: Optional[str] = None,
        expiration_date: Optional[int] = None,
        created_at: Optional[int] = None,
        start_date: Optional[int] = None,
        in_progress_at: Optional[int] = None,
        conclusion_date: Optional[int] = None,
        completed_at: Optional[int] = None,
        cancelled_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        justification: Justification = None,
        information_fields: Optional[List[InformationField]] = None,
        creator_user_id: Optional[str] = None,
        creation_date: Optional[int] = None,
    ):
        resolved_id = id or form_id
        resolved_creator = created_by or creator_user_id
        resolved_creation_date = created_at if created_at is not None else creation_date
        resolved_start_date = in_progress_at if in_progress_at is not None else start_date
        resolved_conclusion_date = completed_at if completed_at is not None else conclusion_date
        resolved_description = observation if observation is not None else description

        resolved_updated_at = updated_at
        if resolved_updated_at is None:
            resolved_updated_at = resolved_conclusion_date or resolved_start_date or resolved_creation_date

        self.form_title = form_title
        self.form_id = resolved_id
        self.id = resolved_id
        self.created_by = resolved_creator
        self.user_id = user_id
        self.template = template
        self.area = area
        self.system = system
        self.street = street
        self.city = city
        self.number = number
        self.latitude = latitude
        self.longitude = longitude
        self.description = resolved_description
        self.observation = resolved_description
        self.priority = priority
        self.status = status
        self.expiration_date = expiration_date
        self.created_at = resolved_creation_date
        self.start_date = resolved_start_date
        self.in_progress_at = resolved_start_date
        self.conclusion_date = resolved_conclusion_date
        self.completed_at = resolved_conclusion_date
        self.cancelled_at = cancelled_at
        self.updated_at = resolved_updated_at
        self.justification = justification
        self.sections = sections
        self.information_fields = information_fields

    @staticmethod
    def from_entity(form: Form) -> "FormDynamoDTO":
        return FormDynamoDTO(
            form_title=form.form_title,
            form_id=form.form_id,
            created_by=form.created_by,
            user_id=form.user_id,
            template=form.template,
            area=form.area,
            system=form.system,
            street=form.street,
            city=form.city,
            number=form.number,
            latitude=form.latitude,
            longitude=form.longitude,
            description=form.description,
            priority=form.priority,
            status=form.status,
            expiration_date=form.expiration_date,
            created_at=form.created_at,
            start_date=form.start_date,
            conclusion_date=form.conclusion_date,
            cancelled_at=form.cancelled_at,
            updated_at=form.updated_at,
            justification=form.justification,
            sections=form.sections,
            information_fields=form.information_fields,
        )

    def to_dynamo(self) -> dict:
        return {
            "form_title": self.form_title,
            "form_id": self.form_id,
            "created_by": self.created_by,
            "user_id": self.user_id,
            "template": self.template,
            "area": self.area,
            "system": self.system,
            "street": self.street,
            "city": self.city,
            "number": self.number,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
            "priority": self.priority.value if isinstance(self.priority, PRIORITY) else self.priority,
            "status": self.status.value if isinstance(self.status, FORM_STATUS) else self.status,
            "expiration_date": self.expiration_date,
            "created_at": self.created_at,
            "in_progress_at": self.in_progress_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
            "updated_at": self.updated_at,
            "justification": JustificationDTO.from_entity(self.justification).to_dynamo() if self.justification else None,
            "sections": [
                SectionDTO.from_entity(section).to_dynamo() for section in self.sections
            ],
            "information_fields": [
                InformationFieldDTO.from_entity(information_field).to_dynamo()
                for information_field in self.information_fields
            ] if self.information_fields else None,
        }

    @staticmethod
    def from_dynamo(data: dict) -> "FormDynamoDTO":
        return FormDynamoDTO(
            form_title=data["form_title"],
            form_id=data.get("form_id") or data.get("id"),
            created_by=data.get("created_by"),
            user_id=data["user_id"],
            template=data.get("template"),
            area=data.get("area"),
            system=data["system"],
            street=data["street"],
            city=data["city"],
            number=int(data["number"]) if data.get("number") is not None else None,
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            description=data.get("description") or data.get("observation"),
            priority=PRIORITY(data["priority"]),
            status=FORM_STATUS(data["status"]),
            expiration_date=int(data["expiration_date"]) if data.get("expiration_date") is not None else None,
            created_at=int(data["created_at"]) if data.get("created_at") is not None else None,
            in_progress_at=int(data["in_progress_at"]) if data.get("in_progress_at") is not None else None,
            completed_at=int(data["completed_at"]) if data.get("completed_at") is not None else None,
            cancelled_at=int(data["cancelled_at"]) if data.get("cancelled_at") is not None else None,
            updated_at=int(data["updated_at"]) if data.get("updated_at") is not None else None,
            justification=JustificationDTO.from_dynamo(data["justification"]).to_entity() if data.get("justification") else None,
            sections=[SectionDTO.from_dynamo(section).to_entity() for section in data.get("sections", [])],
            information_fields=[
                InformationFieldDTO.from_dynamo(information_field).to_entity()
                for information_field in data["information_fields"]
            ] if data.get("information_fields") else None,
        )

    def to_entity(self) -> Form:
        return Form(
            form_title=self.form_title,
            form_id=self.form_id,
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
            description=self.description,
            priority=self.priority,
            status=self.status,
            expiration_date=self.expiration_date,
            in_progress_at=self.in_progress_at,
            cancelled_at=self.cancelled_at,
            completed_at=self.completed_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            justification=self.justification,
            sections=self.sections,
            information_fields=self.information_fields,
        )
