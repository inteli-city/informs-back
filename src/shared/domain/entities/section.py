import abc
import copy
from typing import List

from src.shared.domain.entities.field import Field
from src.shared.domain.validators import ensure_non_negative_int
from src.shared.helpers.errors.domain_errors import EntityError

# Teto de instâncias duplicadas por seção. Cada instância clona a seção base
# inteira e é persistida no mesmo item do DynamoDB (limite de 400KB), então
# sem teto uma única submissão poderia inflar o item até falhar a persistência.
MAX_SECTION_INSTANCE = 50


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

        ensure_non_negative_int(section_instance, 'section_instance')
        self.section_instance = section_instance

    def with_instance(self, section_instance: int) -> "Section":
        """Clona a seção como uma nova instância duplicada.

        A instância nova começa com todos os campos vazios: sem isso, ela
        herdaria qualquer valor que a seção base já tivesse (ex.: default
        gravado na criação do form), satisfazendo campos obrigatórios sem o
        preenchedor ter tocado nesta instância específica.
        """
        section = copy.deepcopy(self)
        section.section_instance = section_instance
        for field in section.fields:
            field.set_value(None)
        return section

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
