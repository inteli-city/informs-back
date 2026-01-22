from abc import ABC
from typing import Optional

from src.shared.helpers.errors.domain_errors import EntityError


class ImageUploadBase(ABC):
    filename: str
    mimetype: str

    def __init__(self, filename: str, mimetype: str):
        if not isinstance(filename, str) or not filename:
            raise EntityError("filename")
        if not isinstance(mimetype, str) or not mimetype:
            raise EntityError("mimetype")
        self.filename = filename
        self.mimetype = mimetype

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "mimetype": self.mimetype,
        }


class ImageUploadRequest(ImageUploadBase):
    pass


class ImageUpload(ImageUploadBase):
    @staticmethod
    def _validate_optional_string(value: Optional[str], field_name: str):
        if value is not None and not isinstance(value, str):
            raise EntityError(field_name)

    @staticmethod
    def _validate_optional_int(value: Optional[int], field_name: str):
        if value is not None and not isinstance(value, int):
            raise EntityError(field_name)

    @staticmethod
    def _validate_fields(
        pre_signed_url: str,
        image_path: str,
        image_url: str,
        section_id: Optional[int],
        field_key: Optional[str],
        file_index: Optional[int],
    ):
        if not isinstance(pre_signed_url, str) or not pre_signed_url:
            raise EntityError("pre_signed_url")
        if not isinstance(image_path, str) or not image_path:
            raise EntityError("image_path")
        if not isinstance(image_url, str) or not image_url:
            raise EntityError("image_url")
        ImageUpload._validate_optional_int(section_id, "section_id")
        ImageUpload._validate_optional_string(field_key, "field_key")
        ImageUpload._validate_optional_int(file_index, "file_index")

    def __init__(
        self,
        filename: str,
        mimetype: str,
        pre_signed_url: str,
        image_path: str,
        image_url: str,
        section_id: Optional[int] = None,
        field_key: Optional[str] = None,
        file_index: Optional[int] = None,
    ):
        super().__init__(filename=filename, mimetype=mimetype)
        self._validate_fields(
            pre_signed_url, image_path, image_url,
            section_id, field_key, file_index
        )

        self.pre_signed_url = pre_signed_url
        self.image_path = image_path
        self.image_url = image_url
        self.section_id = section_id
        self.field_key = field_key
        self.file_index = file_index

    def to_dict(self) -> dict:
        payload = super().to_dict()
        payload.update({
            "pre_signed_url": self.pre_signed_url,
            "image_path": self.image_path,
            "image_url": self.image_url,
            "section_id": self.section_id,
            "field_key": self.field_key,
            "file_index": self.file_index,
        })
        return payload
