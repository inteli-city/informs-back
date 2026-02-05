from abc import ABC, abstractmethod


class IFileRepository(ABC):

    @abstractmethod
    def generate_presigned_url(self, file_path: str, mimetype: str, expires_in: int = 3600) -> str:
        pass
