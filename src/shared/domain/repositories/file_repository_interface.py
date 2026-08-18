from abc import ABC, abstractmethod
from typing import Set


class IFileRepository(ABC):

    @abstractmethod
    def generate_presigned_url(self, file_path: str, mimetype: str, expires_in: int = 3600) -> str:
        pass

    @abstractmethod
    def list_file_paths(self, prefix: str) -> Set[str]:
        """
        Keys que existem de verdade sob o prefixo. É a fonte da verdade sobre o
        que chegou ao S3 — o DynamoDB só guarda a URL que o backend prometeu.

        Um LIST por formulário substitui um HEAD por arquivo (38 chamadas viram 1).
        """
        pass
