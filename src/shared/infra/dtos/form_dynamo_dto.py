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
    creator_user_id: str
    created_by: str
    user_id: str
    vinculation_form_id: Optional[str]
    can_vinculate: bool
    template: Optional[str]
    area: Optional[str]
    system: str
    street: str
    city: str
    number: Optional[int]
    latitude: float
    longitude: float
    region: Optional[str]
    description: Optional[str]
    observation: Optional[str]
    priority: PRIORITY
    status: FORM_STATUS
    expiration_date: Optional[int]
    creation_date: int
    created_at: int
    start_date: Optional[int]
    in_progress_at: Optional[int]
    conclusion_date: Optional[int]
    completed_at: Optional[int]
    cancelled_at: Optional[int]
    updated_at: int
    justification: Justification
    comments: Optional[str]
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
        creator_user_id: Optional[str] = None,
        created_by: Optional[str] = None,
        vinculation_form_id: Optional[str] = None,
        can_vinculate: Optional[bool] = None,
        template: Optional[str] = None,
        area: Optional[str] = None,
        number: Optional[int] = None,
        region: Optional[str] = None,
        description: Optional[str] = None,
        observation: Optional[str] = None,
        expiration_date: Optional[int] = None,
        creation_date: Optional[int] = None,
        created_at: Optional[int] = None,
        start_date: Optional[int] = None,
        in_progress_at: Optional[int] = None,
        conclusion_date: Optional[int] = None,
        completed_at: Optional[int] = None,
        cancelled_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        justification: Justification = None,
        comments: Optional[str] = None,
        information_fields: Optional[List[InformationField]] = None,
    ):
        resolved_id = id or form_id
        resolved_creator = created_by or creator_user_id
        resolved_creation_date = created_at if created_at is not None else creation_date
        resolved_start_date = in_progress_at if in_progress_at is not None else start_date
        resolved_conclusion_date = completed_at if completed_at is not None else conclusion_date
        resolved_description = observation if observation is not None else description
        resolved_region = region if region is not None else area

        resolved_updated_at = updated_at
        if resolved_updated_at is None:
            resolved_updated_at = resolved_conclusion_date or resolved_start_date or resolved_creation_date

        self.form_title = form_title
        self.form_id = resolved_id
        self.id = resolved_id
        self.creator_user_id = resolved_creator
        self.created_by = resolved_creator
        self.user_id = user_id
        self.vinculation_form_id = vinculation_form_id
        self.can_vinculate = bool(can_vinculate) if can_vinculate is not None else False
        self.template = template
        self.area = area
        self.system = system
        self.street = street
        self.city = city
        self.number = number
        self.latitude = latitude
        self.longitude = longitude
        self.region = resolved_region
        self.description = resolved_description
        self.observation = resolved_description
        self.priority = priority
        self.status = status
        self.expiration_date = expiration_date
        self.creation_date = resolved_creation_date
        self.created_at = resolved_creation_date
        self.start_date = resolved_start_date
        self.in_progress_at = resolved_start_date
        self.conclusion_date = resolved_conclusion_date
        self.completed_at = resolved_conclusion_date
        self.cancelled_at = cancelled_at
        self.updated_at = resolved_updated_at
        self.justification = justification
        self.comments = comments
        self.sections = sections
        self.information_fields = information_fields

    @staticmethod
    def from_entity(form: Form) -> "FormDynamoDTO":
        return FormDynamoDTO(
            form_title=form.form_title,
            form_id=form.form_id,
            creator_user_id=form.creator_user_id,
            user_id=form.user_id,
            vinculation_form_id=form.vinculation_form_id,
            can_vinculate=form.can_vinculate,
            template=form.template,
            area=form.area,
            system=form.system,
            street=form.street,
            city=form.city,
            number=form.number,
            latitude=form.latitude,
            longitude=form.longitude,
            region=form.region,
            description=form.description,
            priority=form.priority,
            status=form.status,
            expiration_date=form.expiration_date,
            creation_date=form.creation_date,
            start_date=form.start_date,
            conclusion_date=form.conclusion_date,
            cancelled_at=form.cancelled_at,
            updated_at=form.updated_at,
            justification=form.justification,
            comments=form.comments,
            sections=form.sections,
            information_fields=form.information_fields,
        )

    def to_dynamo(self) -> dict:
        return {
            "form_title": self.form_title,
            "form_id": self.form_id,
            "creator_user_id": self.creator_user_id,
            "user_id": self.user_id,
            "vinculation_form_id": self.vinculation_form_id,
            "can_vinculate": self.can_vinculate,
            "template": self.template,
            "area": self.area,
            "system": self.system,
            "street": self.street,
            "city": self.city,
            "number": self.number,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "region": self.region,
            "description": self.description,
            "priority": self.priority.value if isinstance(self.priority, PRIORITY) else self.priority,
            "status": self.status.value if isinstance(self.status, FORM_STATUS) else self.status,
            "expiration_date": self.expiration_date,
            "creation_date": self.creation_date,
            "start_date": self.start_date,
            "conclusion_date": self.conclusion_date,
            "justification": JustificationDTO.from_entity(self.justification).to_dynamo() if self.justification else None,
            "comments": self.comments,
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
        creation_date = data.get("creation_date")
        if creation_date is None:
            creation_date = data.get("created_at")

        start_date = data.get("start_date")
        if start_date is None:
            start_date = data.get("in_progress_at")

        conclusion_date = data.get("conclusion_date")
        if conclusion_date is None:
            conclusion_date = data.get("completed_at")

        return FormDynamoDTO(
            form_title=data["form_title"],
            form_id=data.get("form_id") or data.get("id"),
            creator_user_id=data.get("creator_user_id") or data.get("created_by"),
            user_id=data["user_id"],
            vinculation_form_id=data.get("vinculation_form_id"),
            can_vinculate=data.get("can_vinculate"),
            template=data.get("template"),
            area=data.get("area"),
            system=data["system"],
            street=data["street"],
            city=data["city"],
            number=int(data["number"]) if data.get("number") is not None else None,
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            region=data.get("region"),
            description=data.get("description") or data.get("observation"),
            priority=PRIORITY(data["priority"]),
            status=FORM_STATUS(data["status"]),
            expiration_date=int(data["expiration_date"]) if data.get("expiration_date") is not None else None,
            creation_date=int(creation_date) if creation_date is not None else None,
            start_date=int(start_date) if start_date is not None else None,
            conclusion_date=int(conclusion_date) if conclusion_date is not None else None,
            cancelled_at=int(data["cancelled_at"]) if data.get("cancelled_at") is not None else None,
            updated_at=int(data["updated_at"]) if data.get("updated_at") is not None else None,
            justification=JustificationDTO.from_dynamo(data["justification"]).to_entity() if data.get("justification") else None,
            comments=data.get("comments"),
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
            creator_user_id=self.creator_user_id,
            user_id=self.user_id,
            created_by=self.created_by,
            vinculation_form_id=self.vinculation_form_id,
            can_vinculate=self.can_vinculate,
            template=self.template,
            area=self.area,
            system=self.system,
            street=self.street,
            city=self.city,
            number=self.number,
            latitude=self.latitude,
            longitude=self.longitude,
            region=self.region,
            description=self.description,
            priority=self.priority,
            status=self.status,
            expiration_date=self.expiration_date,
            in_progress_at=self.start_date,
            cancelled_at=self.cancelled_at,
            completed_at=self.conclusion_date,
            created_at=self.creation_date,
            updated_at=self.updated_at,
            justification=self.justification,
            comments=self.comments,
            sections=self.sections,
            information_fields=self.information_fields,
        )
