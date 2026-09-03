from typing import Dict, List, Optional

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import InformationField
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_origin_enum import FormOrigin
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.infra.dtos.information_field_dto import InformationFieldDTO
from src.shared.infra.dtos.justification_dto import JustificationDTO
from src.shared.infra.dtos.section_dto import SectionDTO


class FormDynamoDTO:
    form_title: str
    id: str
    created_by: str
    user_id: Optional[str]
    template: Optional[str]
    area: Optional[str]
    system: str
    street: str
    city: str
    number: Optional[int]
    latitude: float
    longitude: float
    observation: Optional[str]
    priority: Priority
    status: FormStatus
    expiration_date: Optional[int]
    created_at: int
    in_progress_at: Optional[int]
    completed_at: Optional[int]
    cancelled_at: Optional[int]
    updated_at: int
    justification: Justification
    sections: List[Section]
    information_fields: Optional[List[InformationField]]
    external_id: Optional[str]
    origin: Optional[FormOrigin]
    service_type: Optional[str]
    occurred_at: Optional[int]
    scheduled_start_at: Optional[int]
    scheduled_end_at: Optional[int]
    attributes: Dict[str, List[str]]
    completed_by: Optional[str]

    def __init__(
        self,
        form_title: str,
        id: str,
        system: str,
        street: str,
        city: str,
        latitude: float,
        longitude: float,
        priority: Priority,
        status: FormStatus,
        sections: List[Section],
        user_id: Optional[str] = None,
        created_by: Optional[str] = None,
        template: Optional[str] = None,
        area: Optional[str] = None,
        number: Optional[int] = None,
        observation: Optional[str] = None,
        expiration_date: Optional[int] = None,
        created_at: Optional[int] = None,
        in_progress_at: Optional[int] = None,
        completed_at: Optional[int] = None,
        cancelled_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        justification: Justification = None,
        information_fields: Optional[List[InformationField]] = None,
        external_id: Optional[str] = None,
        origin: Optional[FormOrigin] = None,
        service_type: Optional[str] = None,
        occurred_at: Optional[int] = None,
        scheduled_start_at: Optional[int] = None,
        scheduled_end_at: Optional[int] = None,
        attributes: Optional[Dict[str, List[str]]] = None,
        completed_by: Optional[str] = None,
    ):
        self.form_title = form_title
        self.id = id
        self.created_by = created_by
        self.user_id = user_id
        self.template = template
        self.area = area
        self.system = system
        self.street = street
        self.city = city
        self.number = number
        self.latitude = latitude
        self.longitude = longitude
        self.observation = observation
        self.priority = priority
        self.status = status
        self.expiration_date = expiration_date
        self.created_at = created_at
        self.in_progress_at = in_progress_at
        self.completed_at = completed_at
        self.cancelled_at = cancelled_at
        self.updated_at = updated_at
        self.justification = justification
        self.sections = sections
        self.information_fields = information_fields
        self.external_id = external_id
        self.origin = origin
        self.service_type = service_type
        self.occurred_at = occurred_at
        self.scheduled_start_at = scheduled_start_at
        self.scheduled_end_at = scheduled_end_at
        self.attributes = attributes if attributes is not None else {}
        self.completed_by = completed_by

    @staticmethod
    def from_entity(form: Form) -> "FormDynamoDTO":
        return FormDynamoDTO(
            form_title=form.form_title,
            id=form.id,
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
            observation=form.observation,
            priority=form.priority,
            status=form.status,
            expiration_date=form.expiration_date,
            created_at=form.created_at,
            in_progress_at=form.in_progress_at,
            completed_at=form.completed_at,
            cancelled_at=form.cancelled_at,
            updated_at=form.updated_at,
            justification=form.justification,
            sections=form.sections,
            information_fields=form.information_fields,
            external_id=form.external_id,
            origin=form.origin,
            service_type=form.service_type,
            occurred_at=form.occurred_at,
            scheduled_start_at=form.scheduled_start_at,
            scheduled_end_at=form.scheduled_end_at,
            attributes=form.attributes,
            completed_by=form.completed_by,
        )

    def to_dynamo(self) -> dict:
        return {
            "form_title": self.form_title,
            "created_by": self.created_by,
            "user_id": self.user_id,
            "template": self.template,
            "area": self.area,
            "system": self.system,
            "street": self.street,
            "city": self.city,
            "number": self.number,
            "observation": self.observation,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "priority": self.priority.value if isinstance(self.priority, Priority) else self.priority,
            "status": self.status.value if isinstance(self.status, FormStatus) else self.status,
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
            "external_id": self.external_id,
            "origin": self.origin.value if isinstance(self.origin, FormOrigin) else self.origin,
            "service_type": self.service_type,
            "occurred_at": self.occurred_at,
            "scheduled_start_at": self.scheduled_start_at,
            "scheduled_end_at": self.scheduled_end_at,
            "attributes": self.attributes,
            "completed_by": self.completed_by,
        }

    @staticmethod
    def from_dynamo(data: dict) -> "FormDynamoDTO":
        pk = data["PK"]
        if not isinstance(pk, str) or not pk.startswith("form#"):
            raise KeyError("PK")
        form_id = pk.split("form#", 1)[1]

        return FormDynamoDTO(
            form_title=data["form_title"],
            id=form_id,
            created_by=data["created_by"],
            user_id=data.get("user_id"),
            template=data.get("template"),
            area=data.get("area"),
            system=data["system"],
            street=data["street"],
            city=data["city"],
            number=int(data["number"]) if data.get("number") is not None else None,
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            observation=data.get("observation"),
            priority=Priority(data["priority"]),
            status=FormStatus(data["status"]),
            expiration_date=int(data["expiration_date"]) if data.get("expiration_date") is not None else None,
            created_at=int(data["created_at"]),
            in_progress_at=int(data["in_progress_at"]) if data.get("in_progress_at") is not None else None,
            completed_at=int(data["completed_at"]) if data.get("completed_at") is not None else None,
            cancelled_at=int(data["cancelled_at"]) if data.get("cancelled_at") is not None else None,
            updated_at=int(data["updated_at"]),
            justification=JustificationDTO.from_dynamo(data["justification"]).to_entity() if data.get("justification") else None,
            sections=[SectionDTO.from_dynamo(section).to_entity() for section in data.get("sections", [])],
            information_fields=[
                InformationFieldDTO.from_dynamo(information_field).to_entity()
                for information_field in data["information_fields"]
            ] if data.get("information_fields") else None,
            external_id=data.get("external_id"),
            origin=FormOrigin(data["origin"]) if data.get("origin") is not None else None,
            service_type=data.get("service_type"),
            occurred_at=int(data["occurred_at"]) if data.get("occurred_at") is not None else None,
            scheduled_start_at=int(data["scheduled_start_at"]) if data.get("scheduled_start_at") is not None else None,
            scheduled_end_at=int(data["scheduled_end_at"]) if data.get("scheduled_end_at") is not None else None,
            attributes=dict(data.get("attributes") or {}),
            completed_by=data.get("completed_by"),
        )

    def to_entity(self) -> Form:
        return Form(
            form_title=self.form_title,
            id=self.id,
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
            observation=self.observation,
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
            external_id=self.external_id,
            origin=self.origin,
            service_type=self.service_type,
            occurred_at=self.occurred_at,
            scheduled_start_at=self.scheduled_start_at,
            scheduled_end_at=self.scheduled_end_at,
            attributes=self.attributes,
            completed_by=self.completed_by,
        )

    def to_dict(self) -> dict:
        return {
            "form_title": self.form_title,
            "id": self.id,
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
            "observation": self.observation,
            "priority": self.priority.value if isinstance(self.priority, Priority) else self.priority,
            "status": self.status.value if isinstance(self.status, FormStatus) else self.status,
            "expiration_date": self.expiration_date,
            "created_at": self.created_at,
            "in_progress_at": self.in_progress_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
            "updated_at": self.updated_at,
            "justification": JustificationDTO.from_entity(self.justification).to_dict() if self.justification else None,
            "sections": [
                SectionDTO.from_entity(section).to_dict() for section in self.sections
            ],
            "information_fields": [
                InformationFieldDTO.from_entity(information_field).to_dict()
                for information_field in self.information_fields
            ] if self.information_fields else None,
        }
