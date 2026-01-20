from typing import Optional

from src.shared.helpers.errors.domain_errors import EntityError


class ImageUpload:
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
        if not isinstance(mimetype, str) or not mimetype:
            raise EntityError("mimetype")
        if not isinstance(pre_signed_url, str) or not pre_signed_url:
            raise EntityError("pre_signed_url")
        if not isinstance(image_path, str) or not image_path:
            raise EntityError("image_path")
        if not isinstance(image_url, str) or not image_url:
            raise EntityError("image_url")
        if filename is not None and not isinstance(filename, str):
            raise EntityError("filename")
        if section_id is not None and not isinstance(section_id, int):
            raise EntityError("section_id")
        if field_key is not None and not isinstance(field_key, str):
            raise EntityError("field_key")
        if file_index is not None and not isinstance(file_index, int):
            raise EntityError("file_index")

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
