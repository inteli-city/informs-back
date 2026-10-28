from src.shared.helpers.contracts.schemas.justification import JustificationOptionSchema
from pydantic import AliasChoices, Field, StrictBool

from src.shared.helpers.contracts.base import RequestContractModel
from src.shared.helpers.contracts.schemas.template import TemplateSchema, TemplateSectionSchema


class UpdateTemplateRequestSchema(RequestContractModel):
    name: str
    system: str
    description: str | None = None
    is_active: StrictBool = Field(
        alias="isActive",
        validation_alias=AliasChoices("isActive", "is_active"),
        serialization_alias="isActive",
    )
    sections: list[TemplateSectionSchema]
    justification_options: list[JustificationOptionSchema] | None = None
    new_version: StrictBool = Field(
        default=False,
        description=(
            "Grava as seções e os motivos como uma nova versão. Obrigatório quando "
            "o template já tem formulários e esse conteúdo muda (sem ele, 409). "
            "Nome, descrição e ativo mudam sem nova versão."
        ),
    )


class UpdateTemplateResponseSchema(TemplateSchema):
    pass
