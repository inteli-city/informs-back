from src.shared.domain.entities.image_upload import ImageUpload


class CancelFormViewmodel:
    def __init__(self, image: ImageUpload):
        self.image = image

    def to_dict(self) -> dict:
        return {
            "image": self.image.to_dict() if self.image else None
        }
