from typing import Optional

from src.shared.domain.entities.file_upload import FileUpload
from src.shared.helpers.contracts.endpoints.cancel_form_contract import CancelFormResponseSchema


class CancelFormViewmodel:
    def __init__(self, file_upload: Optional[FileUpload]):
        self.file_upload = file_upload

    def to_dict(self) -> dict:
        files = []
        if self.file_upload:
            files = [
                self.file_upload.to_dict() if isinstance(self.file_upload, FileUpload) else self.file_upload
            ]
        payload = {
            "files": files
        }
        return CancelFormResponseSchema.model_validate(payload).model_dump()
