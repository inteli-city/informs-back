import abc
from typing import List

from src.shared.domain.entities.field import Field
from src.shared.helpers.errors.domain_errors import EntityError


class Section(abc.ABC):
    section_id: int
    fields: List[Field]
    is_duplicable: bool
    section_instance: int

    def __init__(
        self,
        section_id: int,
        fields: List[Field],
        is_duplicable: bool = False,
        section_instance: int = 0,
    ):
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

        if not isinstance(is_duplicable, bool):
            raise EntityError('is_duplicable deve ser um booleano')
        self.is_duplicable = is_duplicable

        if not isinstance(section_instance, int) or isinstance(section_instance, bool) or section_instance < 0:
            raise EntityError('section_instance deve ser um inteiro não negativo')
        self.section_instance = section_instance

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
