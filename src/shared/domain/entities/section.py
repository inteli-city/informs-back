import abc
from typing import List

from src.shared.domain.entities.field import Field
from src.shared.helpers.errors.domain_errors import EntityError


class Section(abc.ABC):
    section_id: int
    fields: List[Field]

    def __init__(self, section_id: int, fields: List[Field]):
        if not isinstance(section_id, int):
            raise EntityError('ID da seção deve ser um número inteiro')
        self.section_id = section_id

        if not isinstance(fields, list):
            raise EntityError('Campos da seção devem ser uma lista')
        if not fields:
            raise EntityError('A seção deve ter ao menos um campo')
        if not all(isinstance(field, Field) for field in fields):
            raise EntityError('Todos os campos da seção devem ser instâncias válidas de Field')
        self._ensure_unique_field_keys(fields)
        self.fields = fields

    def _ensure_unique_field_keys(self, fields: List[Field]) -> None:
        seen = set()
        duplicated = []
        for field in fields:
                key = field.key
                if key in seen:
                    if key not in duplicated:
                        duplicated.append(key)
                else:
                    seen.add(key)
        if duplicated:
            raise EntityError(f'Chaves de campo duplicadas na seção: {duplicated}')
