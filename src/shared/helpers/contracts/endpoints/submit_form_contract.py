from typing import Any

from pydantic import BaseModel, Field

from src.shared.helpers.contracts.schemas.file_upload import FileUploadSchema


class SubmitFormFieldFlatSchema(BaseModel):
    section_id: int
    field_key: str
    value: Any | None = None


class SubmitFormRequestSchema(BaseModel):
    fields: list[SubmitFormFieldFlatSchema]
    completed_at: int


class SubmitFormResponseSchema(BaseModel):
    files: list[FileUploadSchema] = Field(default_factory=list)
