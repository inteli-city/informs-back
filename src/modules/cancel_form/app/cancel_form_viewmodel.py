from typing import Optional

from src.shared.domain.entities.file_upload import FileUpload


class CancelFormViewmodel:
    def __init__(self, file_upload: Optional[FileUpload]):
        self.file_upload = file_upload

    def to_dict(self) -> dict:
        files = []
        if self.file_upload:
            files = [
                self.file_upload.to_dict() if isinstance(self.file_upload, FileUpload) else self.file_upload
            ]
        return {
            "files": files
        }
