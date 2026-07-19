from pydantic import Field

from src.shared.helpers.contracts.base import NonNegativeStrictInt, RequestContractModel, ResponseContractModel
from .field import GenericFieldSchema
from .information_field import InformationFieldSchema
from .justification import JustificationSchema


class FormSectionSchema(RequestContractModel):
    section_id: int
    fields: list[GenericFieldSchema]
    is_duplicable: bool = False
    section_instance: NonNegativeStrictInt = Field(
        default=0,
        description=(
            "Somente leitura: preenchido nas respostas para identificar instâncias "
            "duplicadas (0 = seção original). Na criação do formulário deve ser 0 "
            "(default) — instâncias novas são criadas apenas na submissão."
        ),
    )


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
