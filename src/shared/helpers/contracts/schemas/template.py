from src.shared.helpers.contracts.schemas.justification import JustificationOptionSchema
from pydantic import Field

from src.shared.helpers.contracts.base import NonNegativeStrictInt, RequestContractModel, ResponseContractModel
from .field import GenericFieldSchema


class TemplateSectionSchema(RequestContractModel):
    section_id: int
    fields: list[GenericFieldSchema]
    is_duplicable: bool = False
    section_instance: NonNegativeStrictInt = Field(
        default=0,
        description=(
            "Somente leitura: preenchido nas respostas para identificar instâncias "
            "duplicadas (0 = seção original). Em create/update de template deve ser 0 "
            "(default) — instâncias novas são criadas apenas na submissão do formulário."
        ),
    )


class TemplateSchema(ResponseContractModel):
    id: str
    name: str
    system: str
    description: str | None = None
    is_active: bool
    sections: list[TemplateSectionSchema]
    # Motivos de cancelamento herdados pelos formulários criados deste template.
    justification_options: list[JustificationOptionSchema] = Field(default_factory=list)
    created_by: str
    created_at: int
    updated_at: int
