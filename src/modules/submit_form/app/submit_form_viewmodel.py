from src.shared.domain.entities.image_upload import ImageUpload


class SubmitFormViewmodel:
    def __init__(self, images: list[ImageUpload]):
        self.images = images

    def to_dict(self) -> dict:
        return {
            "images": [image.to_dict() for image in self.images]
        }
