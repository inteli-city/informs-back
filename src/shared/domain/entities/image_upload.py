from typing import Optional

from src.shared.helpers.errors.domain_errors import EntityError


class ImageUpload:
    @staticmethod
    def _validate_required_string(value: str, field_name: str):
        if not isinstance(value, str) or not value:
            raise EntityError(field_name)

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
        mimetype: str,
        pre_signed_url: str,
        image_path: str,
        image_url: str,
        filename: Optional[str],
        section_id: Optional[int],
        field_key: Optional[str],
        file_index: Optional[int],
    ):
        ImageUpload._validate_required_string(mimetype, "mimetype")
        ImageUpload._validate_required_string(pre_signed_url, "pre_signed_url")
        ImageUpload._validate_required_string(image_path, "image_path")
        ImageUpload._validate_required_string(image_url, "image_url")
        ImageUpload._validate_optional_string(filename, "filename")
        ImageUpload._validate_optional_int(section_id, "section_id")
        ImageUpload._validate_optional_string(field_key, "field_key")
        ImageUpload._validate_optional_int(file_index, "file_index")

    def __init__(
        self,
        mimetype: str,
        pre_signed_url: str,
        image_path: str,
        image_url: str,
        filename: Optional[str] = None,
        section_id: Optional[int] = None,
        field_key: Optional[str] = None,
        file_index: Optional[int] = None,
    ):
        self._validate_fields(
            mimetype, pre_signed_url, image_path, image_url,
            filename, section_id, field_key, file_index
        )

        self.filename = filename
        self.mimetype = mimetype
        self.pre_signed_url = pre_signed_url
        self.image_path = image_path
        self.image_url = image_url
        self.section_id = section_id
        self.field_key = field_key
        self.file_index = file_index

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "mimetype": self.mimetype,
            "pre_signed_url": self.pre_signed_url,
            "image_path": self.image_path,
            "image_url": self.image_url,
            "section_id": self.section_id,
            "field_key": self.field_key,
            "file_index": self.file_index,
        }
