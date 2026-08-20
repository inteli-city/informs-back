from typing import List

from src.shared.domain.entities.file_upload import FileUpload
from src.shared.helpers.contracts.endpoints.refresh_presign_contract import RefreshPresignResponseSchema


class RefreshPresignViewmodel:
    def __init__(self, files: List[FileUpload]):
        self.files = files

    def to_dict(self) -> dict:
        payload = {
            "files": [file.to_dict() for file in self.files]
        }
        return RefreshPresignResponseSchema.model_validate(payload).model_dump()
