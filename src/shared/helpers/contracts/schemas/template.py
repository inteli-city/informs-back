from pydantic import BaseModel

from .field import GenericFieldSchema


class TemplateSectionSchema(BaseModel):
    section_id: int
    fields: list[GenericFieldSchema]


class TemplateSchema(BaseModel):
    id: str
    name: str
    system: str
    description: str | None = None
    is_active: bool
    sections: list[TemplateSectionSchema]
    created_by: str
    created_at: int
    updated_at: int
