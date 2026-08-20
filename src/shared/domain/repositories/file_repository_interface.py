from abc import ABC, abstractmethod
from typing import Optional, Set

# A presigned URL é assinada com as credenciais temporárias do role da Lambda, e
# a doc da AWS é explícita: "IAM role credentials - the presigned URL expires
# when the role session expires, even if you specify a longer expiration time".
# Ou seja, 6h é um teto de melhor esforço, não uma garantia. É folga para o app
# terminar a fila de upload, não substituto do refresh-presign.
DEFAULT_PRESIGN_EXPIRES_IN = 21600


class IFileRepository(ABC):

    @abstractmethod
    def generate_presigned_url(self, file_path: str, mimetype: str, expires_in: int = DEFAULT_PRESIGN_EXPIRES_IN, checksum_sha256: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def get_file_metadata(self, file_path: str) -> dict:
        """Metadados do objeto para reconciliação de integridade."""
        pass

    @abstractmethod
    def list_file_paths(self, prefix: str) -> Set[str]:
        """
        Keys que existem de verdade sob o prefixo. É a fonte da verdade sobre o
        que chegou ao S3 — o DynamoDB só guarda a URL que o backend prometeu.

        Um LIST por formulário encontra ausências em lote; HEAD fica reservado
        aos novos arquivos que trouxeram expectativa de integridade.
        """
        pass
