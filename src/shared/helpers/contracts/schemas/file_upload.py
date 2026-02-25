from pydantic import BaseModel


class FileUploadParamsSchema(BaseModel):
    filename: str
    mimetype: str


class FileUploadSchema(BaseModel):
    filename: str
    mimetype: str
    pre_signed_url: str
    file_path: str
    file_url: str
    section_id: int | None = None
    field_key: str | None = None
    file_index: int | None = None
