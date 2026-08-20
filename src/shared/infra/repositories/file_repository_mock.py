from typing import Optional, Set

from src.shared.domain.repositories.file_repository_interface import DEFAULT_PRESIGN_EXPIRES_IN, IFileRepository


class FileRepositoryMock(IFileRepository):

    def __init__(self):
        # Keys "presentes no bucket"; o teste popula o que quer que exista.
        self.existing_file_paths: Set[str] = set()
        self.list_calls: list[str] = []
        self.file_metadata: dict[str, dict] = {}
        self.head_calls: list[str] = []

    def generate_presigned_url(self, file_path: str, mimetype: str, expires_in: int = DEFAULT_PRESIGN_EXPIRES_IN, checksum_sha256: Optional[str] = None) -> str:
        checksum = f"&checksum_sha256={checksum_sha256}" if checksum_sha256 else ""
        return f"https://mock-presigned-url/{file_path}?mimetype={mimetype}&expires_in={expires_in}{checksum}"

    def list_file_paths(self, prefix: str) -> Set[str]:
        self.list_calls.append(prefix)
        return {path for path in self.existing_file_paths if path.startswith(prefix)}

    def get_file_metadata(self, file_path: str) -> dict:
        self.head_calls.append(file_path)
        return self.file_metadata.get(file_path, {})
