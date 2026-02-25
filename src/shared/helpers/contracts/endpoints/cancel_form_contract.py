from pydantic import BaseModel, Field

from src.shared.helpers.contracts.schemas.file_upload import FileUploadParamsSchema, FileUploadSchema


class CancelFormRequestSchema(BaseModel):
    option: str
    text: str | None = None
    file: FileUploadParamsSchema | None = None
    cancelled_at: int | None = None


class CancelFormResponseSchema(BaseModel):
    files: list[FileUploadSchema] = Field(default_factory=list)
