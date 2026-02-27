from src.shared.domain.entities.file_upload import FileUpload
from src.shared.helpers.contracts.endpoints.submit_form_contract import SubmitFormResponseSchema


class SubmitFormViewmodel:
    def __init__(self, files: list[FileUpload]):
        self.files = files

    def to_dict(self) -> dict:
        payload = {
            "files": [file.to_dict() for file in self.files]
        }
        return SubmitFormResponseSchema.model_validate(payload).model_dump()
