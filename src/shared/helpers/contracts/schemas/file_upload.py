from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


class FileUploadParamsSchema(RequestContractModel):
    filename: str
    mimetype: str


class FileUploadSchema(ResponseContractModel):
    filename: str
    mimetype: str
    pre_signed_url: str
    file_path: str
    file_url: str
    section_id: int | None = None
    field_key: str | None = None
    file_index: int | None = None
