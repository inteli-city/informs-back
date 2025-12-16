import abc
from typing import List

from src.shared.domain.entities.field import Field
from src.shared.helpers.errors.domain_errors import EntityError


class Section(abc.ABC):
    section_id: int
    fields: List[Field]

    def __init__(self, section_id, fields: List[Field]):
        if not isinstance(section_id, (int, str)):
            raise EntityError('section_id')
        self.section_id = section_id

        if not isinstance(fields, list):
            raise EntityError('fields')
        if not fields:
            raise EntityError('fields')
        if not all(isinstance(field, Field) for field in fields):
            raise EntityError('fields')
        self.fields = fields
