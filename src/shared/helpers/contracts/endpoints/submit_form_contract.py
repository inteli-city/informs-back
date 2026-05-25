from typing import Any

from pydantic import Field

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel
from src.shared.helpers.contracts.schemas.file_upload import FileUploadSchema


class SubmitFormFieldFlatSchema(RequestContractModel):
    section_id: int
    section_instance: int = 0
    field_key: str
    value: Any | None = None


class SubmitFormRequestSchema(RequestContractModel):
    fields: list[SubmitFormFieldFlatSchema]
    completed_at: int


class SubmitFormResponseSchema(ResponseContractModel):
    files: list[FileUploadSchema] = Field(default_factory=list)
