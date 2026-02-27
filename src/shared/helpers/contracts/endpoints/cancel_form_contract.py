from pydantic import AliasChoices, Field

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel
from src.shared.helpers.contracts.schemas.file_upload import FileUploadParamsSchema, FileUploadSchema


class CancelFormRequestSchema(RequestContractModel):
    option: str
    text: str | None = Field(
        default=None,
        validation_alias=AliasChoices("text", "justification_text"),
        serialization_alias="text",
    )
    file: FileUploadParamsSchema | None = Field(
        default=None,
        validation_alias=AliasChoices("file", "justification_image"),
        serialization_alias="file",
    )
    cancelled_at: int | None = None


class CancelFormResponseSchema(ResponseContractModel):
    files: list[FileUploadSchema] = Field(default_factory=list)
