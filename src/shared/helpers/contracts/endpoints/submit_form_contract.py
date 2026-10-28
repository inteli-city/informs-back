from typing import Any

from pydantic import Field

from src.shared.domain.entities.section import MAX_SECTION_INSTANCE
from src.shared.helpers.contracts.base import NonNegativeStrictInt, RequestContractModel, ResponseContractModel
from src.shared.helpers.contracts.schemas.file_upload import FileUploadSchema


class SubmitFormFieldFlatSchema(RequestContractModel):
    section_id: int
    section_instance: NonNegativeStrictInt = Field(default=0, le=MAX_SECTION_INSTANCE)
    field_key: str
    value: Any | None = None


class SubmitFormRequestSchema(RequestContractModel):
    fields: list[SubmitFormFieldFlatSchema]
    completed_at: int
    template_version: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Versão do template em que o formulário estava quando foi preenchido. "
            "Se o formulário recebeu uma versão mais nova desde então, o envio é "
            "aceito assim mesmo: respostas de campos que não existem mais são "
            "ignoradas e os campos obrigatórios novos não são exigidos."
        ),
    )


class SubmitFormResponseSchema(ResponseContractModel):
    files: list[FileUploadSchema] = Field(default_factory=list)
