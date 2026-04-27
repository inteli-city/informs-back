from abc import ABC
from typing import Optional

from src.shared.helpers.errors.domain_errors import EntityError


class FileUploadBase(ABC):
    filename: str
    mimetype: str

    def __init__(self, filename: str, mimetype: str):
        if not isinstance(filename, str) or not filename:
            raise EntityError("Nome do arquivo deve ser uma string não vazia")
        if not isinstance(mimetype, str) or not mimetype:
            raise EntityError("Tipo MIME deve ser uma string não vazia")
        self.filename = filename
        self.mimetype = mimetype

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "mimetype": self.mimetype,
        }


class FileUploadRequest(FileUploadBase):
    pass


class FileUpload(FileUploadBase):
    @staticmethod
    def _validate_optional_string(value: Optional[str], field_name: str):
        if value is not None and not isinstance(value, str):
            raise EntityError(f"Campo '{field_name}' deve ser uma string")

    @staticmethod
    def _validate_optional_int(value: Optional[int], field_name: str):
        if value is not None and not isinstance(value, int):
            raise EntityError(f"Campo '{field_name}' deve ser um inteiro")

    @staticmethod
    def _validate_fields(
        pre_signed_url: str,
        file_path: str,
        file_url: str,
        section_id: Optional[int],
        field_key: Optional[str],
        file_index: Optional[int],
    ):
        if not isinstance(pre_signed_url, str) or not pre_signed_url:
            raise EntityError("URL pré-assinada deve ser uma string não vazia")
        if not isinstance(file_path, str) or not file_path:
            raise EntityError("Caminho do arquivo deve ser uma string não vazia")
        if not isinstance(file_url, str) or not file_url:
            raise EntityError("URL do arquivo deve ser uma string não vazia")
        FileUpload._validate_optional_int(section_id, "section_id")
        FileUpload._validate_optional_string(field_key, "field_key")
        FileUpload._validate_optional_int(file_index, "file_index")

    def __init__(
        self,
        filename: str,
        mimetype: str,
        pre_signed_url: str,
        file_path: str,
        file_url: str,
        section_id: Optional[int] = None,
        field_key: Optional[str] = None,
        file_index: Optional[int] = None,
    ):
        super().__init__(filename=filename, mimetype=mimetype)
        self._validate_fields(
            pre_signed_url, file_path, file_url,
            section_id, field_key, file_index
        )

        self.pre_signed_url = pre_signed_url
        self.file_path = file_path
        self.file_url = file_url
        self.section_id = section_id
        self.field_key = field_key
        self.file_index = file_index

    def to_dict(self) -> dict:
        payload = super().to_dict()
        payload.update({
            "pre_signed_url": self.pre_signed_url,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "section_id": self.section_id,
            "field_key": self.field_key,
            "file_index": self.file_index,
        })
        return payload
