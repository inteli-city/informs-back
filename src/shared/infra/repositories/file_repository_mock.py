from src.shared.domain.repositories.file_repository_interface import IFileRepository


class FileRepositoryMock(IFileRepository):

    def generate_presigned_url(self, file_path: str, mimetype: str, expires_in: int = 3600) -> str:
        return f"https://mock-presigned-url/{file_path}?mimetype={mimetype}&expires_in={expires_in}"
