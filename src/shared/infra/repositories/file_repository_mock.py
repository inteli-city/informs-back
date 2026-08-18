from typing import Set

from src.shared.domain.repositories.file_repository_interface import IFileRepository


class FileRepositoryMock(IFileRepository):

    def __init__(self):
        # Keys "presentes no bucket"; o teste popula o que quer que exista.
        self.existing_file_paths: Set[str] = set()
        self.list_calls: list[str] = []

    def generate_presigned_url(self, file_path: str, mimetype: str, expires_in: int = 3600) -> str:
        return f"https://mock-presigned-url/{file_path}?mimetype={mimetype}&expires_in={expires_in}"

    def list_file_paths(self, prefix: str) -> Set[str]:
        self.list_calls.append(prefix)
        return {path for path in self.existing_file_paths if path.startswith(prefix)}
