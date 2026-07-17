from pydantic import Field, StrictInt

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel
from .field import GenericFieldSchema
from .information_field import InformationFieldSchema
from .justification import JustificationSchema


class FormSectionSchema(RequestContractModel):
    section_id: int
    fields: list[GenericFieldSchema]
    is_duplicable: bool = False
    section_instance: StrictInt = Field(default=0, ge=0)


class FormResponseSchema(ResponseContractModel):
    id: str
    status: str
    form_title: str
    user_id: str
    template: str | None = None
    area: str | None = None
    system: str
    city: str
    street: str
    latitude: float
    longitude: float
    priority: int
    observation: str | None = None
    expiration_date: int | None = None
    justification: JustificationSchema
    sections: list[FormSectionSchema]
    in_progress_at: int | None = None
    cancelled_at: int | None = None
    completed_at: int | None = None
    created_by: str
    created_at: int
    updated_at: int
    information_fields: list[InformationFieldSchema] | None = None
    number: int | None = None
