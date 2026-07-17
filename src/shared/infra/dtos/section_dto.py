from typing import List

from src.shared.domain.entities.field import Field
from src.shared.domain.entities.section import Section
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.infra.dtos.field_dto import FieldDTO

class SectionDTO:
    section_id: str
    fields: List[Field]
    is_duplicable: bool
    section_instance: int

    def __init__(self, section_id: str, fields: List[Field], is_duplicable: bool = False, section_instance: int = 0):
        self.section_id = section_id
        self.fields = fields
        self.is_duplicable = is_duplicable
        self.section_instance = section_instance

    @staticmethod
    def from_request(section_dict: dict) -> "SectionDTO":
        if 'section_id' not in section_dict:
            raise MissingParameters('section_id')
        section_id = section_dict['section_id']

        if 'fields' not in section_dict or not section_dict['fields']:
            raise MissingParameters('fields')
        fields_data = section_dict['fields']

        fields = [FieldDTO.from_dynamo(field_dict=field_data).to_entity() for field_data in fields_data]

        # section_instance só é criado via submissão (Form._materialize_section_instance).
        # Aceitar um valor diferente de 0 aqui daria a impressão de que a criação
        # controla a instância, mas quebraria a suposição de apply_field_values de
        # que toda seção base (usada para clonar instâncias novas) está em instância 0.
        section_instance = section_dict.get('section_instance', 0)
        if section_instance != 0:
            raise EntityError(
                "section_instance deve ser 0 na criação/atualização — "
                "instâncias duplicadas são criadas apenas na submissão do formulário"
            )

        return SectionDTO(
            section_id=section_id,
            fields=fields,
            is_duplicable=section_dict.get('is_duplicable', False),
            section_instance=section_instance,
        )

    @staticmethod
    def from_entity(section: Section) -> "SectionDTO":
        return SectionDTO(
            section_id=str(section.section_id),
            fields=section.fields,
            is_duplicable=section.is_duplicable,
            section_instance=section.section_instance,
        )

    @staticmethod
    def from_dynamo(section_dict: dict) -> "SectionDTO":
        return SectionDTO(
            section_id=section_dict['section_id'],
            fields=[FieldDTO.from_dynamo(field_dict=field_data).to_entity() for field_data in section_dict['fields']],
            is_duplicable=section_dict.get('is_duplicable', False),
            section_instance=section_dict.get('section_instance', 0),
        )

    def to_dynamo(self) -> dict:
        return {
            "section_id": self.section_id,
            "is_duplicable": self.is_duplicable,
            "section_instance": self.section_instance,
            "fields": [FieldDTO(field).to_dynamo() for field in self.fields],
        }

    def to_entity(self) -> Section:
        section_id_cast = int(self.section_id) if str(self.section_id).isdigit() else self.section_id
        return Section(
            section_id_cast,
            self.fields,
            is_duplicable=self.is_duplicable,
            section_instance=self.section_instance,
        )
