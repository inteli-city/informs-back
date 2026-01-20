from abc import ABC, abstractmethod


class IImageRepository(ABC):

    @abstractmethod
    def generate_presigned_url(self, image_path: str, mimetype: str, expires_in: int = 3600) -> str:
        pass
