from src.shared.helpers.contracts.schemas.justification import JustificationOptionSchema
from typing import Literal

from pydantic import Field, StrictBool, model_validator

from src.shared.helpers.contracts.base import NonNegativeStrictInt, RequestContractModel, ResponseContractModel
from .field import GenericFieldSchema


class TemplateInformationFieldSchema(RequestContractModel):
    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    information_field_type: Literal["TEXT_INFORMATION_FIELD", "MAP_INFORMATION_FIELD", "FILE_INFORMATION_FIELD", "URL_INFORMATION_FIELD"]
    required: StrictBool = False
    file_type: Literal["IMAGE", "DOCUMENT"] | None = None

    @model_validator(mode="after")
    def validate_file_type(self):
        if self.file_type is not None and self.information_field_type != "FILE_INFORMATION_FIELD":
            raise ValueError("file_type é exclusivo de campos de arquivo")
        return self


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
    information_fields: list[TemplateInformationFieldSchema] = Field(default_factory=list)
    created_by: str
    created_at: int
    updated_at: int
    version: int = Field(
        default=1,
        description=(
            "Versão do conteúdo que os formulários copiam (seções e motivos). Sobe "
            "quando o template já tem formulários e esse conteúdo muda — os "
            "formulários existentes ficam na versão em que nasceram até alguém "
            "propagar a nova (POST /templates/{template_id}/propagate)."
        ),
    )
