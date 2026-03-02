from pydantic import AliasChoices, Field, StrictBool

from src.shared.helpers.contracts.base import RequestContractModel
from src.shared.helpers.contracts.schemas.template import TemplateSchema, TemplateSectionSchema


class CreateTemplateRequestSchema(RequestContractModel):
    name: str
    system: str
    description: str | None = None
    is_active: StrictBool = Field(
        alias="isActive",
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )
    sections: list[TemplateSectionSchema]


class CreateTemplateResponseSchema(TemplateSchema):
    pass
