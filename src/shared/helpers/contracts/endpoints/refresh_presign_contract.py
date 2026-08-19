from pydantic import Field

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel
from src.shared.helpers.contracts.schemas.file_upload import FileUploadSchema


class RefreshPresignFileSchema(RequestContractModel):
    """
    O cliente informa o mimetype que vai usar no PUT porque a assinatura é
    específica de Content-Type — deduzir a partir da extensão da key erraria
    nos casos ambíguos e devolveria uma URL que o S3 recusa.
    """
    file_url: str
    mimetype: str


class RefreshPresignRequestSchema(RequestContractModel):
    files: list[RefreshPresignFileSchema] = Field(min_length=1)


class RefreshPresignResponseSchema(ResponseContractModel):
    files: list[FileUploadSchema] = Field(default_factory=list)
