from src.shared.domain.entities.file_upload import FileUpload


class SubmitFormViewmodel:
    def __init__(self, files: list[FileUpload]):
        self.files = files

    def to_dict(self) -> dict:
        return {
            "files": [file.to_dict() for file in self.files]
        }
