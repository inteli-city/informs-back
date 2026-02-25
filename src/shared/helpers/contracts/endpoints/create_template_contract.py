from pydantic import BaseModel

from src.shared.helpers.contracts.schemas.template import TemplateSchema, TemplateSectionSchema


class CreateTemplateRequestSchema(BaseModel):
    name: str
    system: str
    description: str | None = None
    isActive: bool
    sections: list[TemplateSectionSchema]


class CreateTemplateResponseSchema(TemplateSchema):
    pass
