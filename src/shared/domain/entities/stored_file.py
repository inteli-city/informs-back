from typing import Optional

from src.shared.domain.validators import ensure_non_negative_int
from src.shared.helpers.errors.domain_errors import EntityError


class StoredFile:
    """
    Arquivo já registrado no formulário: a URL final gravada no DynamoDB no
    momento do submit, com a origem (seção/campo/índice) que a produziu.

    Existe porque a URL sozinha não diz de onde veio — e tanto a renovação de
    presigned URL quanto a reconciliação com o S3 precisam saber a origem para
    relatar o que está faltando de forma acionável.
    """

    def __init__(
        self,
        file_url: str,
        section_id: Optional[int] = None,
        section_instance: Optional[int] = None,
        field_key: Optional[str] = None,
        file_index: Optional[int] = None,
    ):
        if not isinstance(file_url, str) or not file_url:
            raise EntityError("URL do arquivo deve ser uma string não vazia")
        if section_id is not None and (not isinstance(section_id, int) or isinstance(section_id, bool)):
            raise EntityError("Campo 'section_id' deve ser um inteiro")
        if field_key is not None and not isinstance(field_key, str):
            raise EntityError("Campo 'field_key' deve ser uma string")
        ensure_non_negative_int(section_instance, "Campo 'section_instance'", allow_none=True)
        ensure_non_negative_int(file_index, "Campo 'file_index'", allow_none=True)

        self.file_url = file_url
        self.section_id = section_id
        self.section_instance = section_instance
        self.field_key = field_key
        self.file_index = file_index

    def to_dict(self) -> dict:
        return {
            "file_url": self.file_url,
            "section_id": self.section_id,
            "section_instance": self.section_instance,
            "field_key": self.field_key,
            "file_index": self.file_index,
        }
