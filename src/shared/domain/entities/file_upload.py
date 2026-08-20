from abc import ABC
import base64
import binascii
from typing import Optional

from src.shared.domain.validators import ensure_non_negative_int
from src.shared.helpers.errors.domain_errors import EntityError


class FileUploadBase(ABC):
    filename: str
    mimetype: str
    size_bytes: Optional[int]
    checksum_sha256: Optional[str]

    def __init__(
        self,
        filename: str,
        mimetype: str,
        size_bytes: Optional[int] = None,
        checksum_sha256: Optional[str] = None,
    ):
        if not isinstance(filename, str) or not filename:
            raise EntityError("Nome do arquivo deve ser uma string não vazia")
        if not isinstance(mimetype, str) or not mimetype:
            raise EntityError("Tipo MIME deve ser uma string não vazia")
        if size_bytes is not None and (not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0):
            raise EntityError("Tamanho do arquivo deve ser um inteiro não negativo")
        if checksum_sha256 is not None:
            if not isinstance(checksum_sha256, str):
                raise EntityError("Checksum SHA-256 deve ser uma string")
            try:
                if len(base64.b64decode(checksum_sha256, validate=True)) != 32:
                    raise ValueError
            except (ValueError, binascii.Error):
                raise EntityError("Checksum SHA-256 deve ser Base64 válido de 32 bytes")
        self.filename = filename
        self.mimetype = mimetype
        self.size_bytes = size_bytes
        self.checksum_sha256 = checksum_sha256

    def to_dict(self) -> dict:
        payload = {
            "filename": self.filename,
            "mimetype": self.mimetype,
        }
        if self.size_bytes is not None:
            payload["size_bytes"] = self.size_bytes
        if self.checksum_sha256 is not None:
            payload["checksum_sha256"] = self.checksum_sha256
        return payload


class FileUploadRequest(FileUploadBase):
    pass


class FileUpload(FileUploadBase):
    @staticmethod
    def _validate_optional_string(value: Optional[str], field_name: str):
        if value is not None and not isinstance(value, str):
            raise EntityError(f"Campo '{field_name}' deve ser uma string")

    @staticmethod
    def _validate_optional_int(value: Optional[int], field_name: str):
        if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
            raise EntityError(f"Campo '{field_name}' deve ser um inteiro")

    @staticmethod
    def _validate_fields(
        pre_signed_url: str,
        file_path: str,
        file_url: str,
        section_id: Optional[int],
        field_key: Optional[str],
        file_index: Optional[int],
        section_instance: Optional[int],
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
        ensure_non_negative_int(section_instance, "Campo 'section_instance'", allow_none=True)

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
        section_instance: Optional[int] = None,
        size_bytes: Optional[int] = None,
        checksum_sha256: Optional[str] = None,
    ):
        super().__init__(filename=filename, mimetype=mimetype, size_bytes=size_bytes, checksum_sha256=checksum_sha256)
        self._validate_fields(
            pre_signed_url, file_path, file_url,
            section_id, field_key, file_index, section_instance
        )

        self.pre_signed_url = pre_signed_url
        self.file_path = file_path
        self.file_url = file_url
        self.section_id = section_id
        self.field_key = field_key
        self.file_index = file_index
        self.section_instance = section_instance

    def to_dict(self) -> dict:
        payload = super().to_dict()
        payload.update({
            "pre_signed_url": self.pre_signed_url,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "section_id": self.section_id,
            "section_instance": self.section_instance,
            "field_key": self.field_key,
            "file_index": self.file_index,
        })
        return payload
