from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel
from .field import GenericFieldSchema


class TemplateSectionSchema(RequestContractModel):
    section_id: int
    fields: list[GenericFieldSchema]
    is_duplicable: bool = False
    section_instance: int = 0


class TemplateSchema(ResponseContractModel):
    id: str
    name: str
    system: str
    description: str | None = None
    is_active: bool
    sections: list[TemplateSectionSchema]
    created_by: str
    created_at: int
    updated_at: int
