from typing import List, Optional
from uuid import uuid4
from datetime import datetime, timezone
import uuid

from src.shared.domain.entities.justification import JustificationOption
from src.shared.domain.entities.file_upload import FileUploadRequest
from src.shared.domain.entities.information_field import FileInformationField, InformationField, TextInformationField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template_information_field import TemplateInformationField
from src.shared.domain.enums.file_source_enum import FileSource
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.helpers.errors.domain_errors import EntityError


class Template:
    id: str
    name: str
    system: str
    description: Optional[str]
    is_active: bool
    sections: List[Section]
    created_by: str
    created_at: int
    updated_at: int
    version: int

    ID_LENGTH = 36

    def __init__(
        self,
        name: str,
        system: str,
        created_by: str,
        sections: List[Section],
        description: Optional[str] = None,
        is_active: bool = True,
        id: Optional[str] = None,
        created_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        justification_options: Optional[List[JustificationOption]] = None,
        version: Optional[int] = None,
        information_fields: Optional[List[TemplateInformationField]] = None,
    ):
        template_identifier = id or str(uuid.uuid4())
        self._validate_id(template_identifier)
        self.id = template_identifier

        self._validate_name(name)
        self.name = name

        self._validate_description(description)
        self.description = description

        self._validate_system(system)
        self.system = system

        self._validate_is_active(is_active)
        self.is_active = is_active

        self._validate_created_by(created_by)
        self.created_by = created_by

        self._validate_created_at(created_at)
        self.created_at = created_at

        self._validate_updated_at(updated_at)
        self.updated_at = updated_at

        self._validate_sections(sections)
        self.sections = sections

        # Motivos de cancelamento que todo formulário criado a partir deste
        # template herda (quando o criador não manda os próprios).
        self.justification_options = self._validate_justification_options(justification_options)

        # Versão do conteúdo copiado para os formulários (seções e motivos de
        # cancelamento). Template sem versão gravada é da época anterior ao
        # versionamento: conta como a 1.
        self.version = self._validate_version(1 if version is None else version)
        self.change_information_fields(information_fields or [])

    def change_information_fields(self, fields: List[TemplateInformationField]) -> None:
        if not isinstance(fields, list) or not all(isinstance(f, TemplateInformationField) for f in fields):
            raise EntityError("Campos informativos devem ser uma lista de definições")
        # A chave identifica o dado no formulário; repetida, duas exigências
        # disputariam o mesmo valor.
        keys = [f.key for f in fields]
        if len(set(keys)) != len(keys):
            raise EntityError("Chaves de campos informativos repetidas")
        self.information_fields = fields

    def validate_information_fields(
        self,
        fields: Optional[List[InformationField]],
        uploads: Optional[List[Optional[FileUploadRequest]]],
    ) -> None:
        """Confere o que quem cria o formulário enviou contra as exigências do
        template. `uploads[i]` é o arquivo declarado para `fields[i]`.

        Só prova a declaração: os bytes do arquivo chegam depois, por PUT."""
        if not self.information_fields:
            return
        uploads = uploads or []
        supplied: dict = {}
        for index, field in enumerate(fields or []):
            # Campo sem chave é o formato anterior: não atende exigência alguma.
            if field.key is None:
                continue
            if field.key in supplied:
                raise EntityError(f"Campo informativo repetido: {field.key}")
            supplied[field.key] = (field, uploads[index] if index < len(uploads) else None)

        for requirement in self.information_fields:
            item = supplied.get(requirement.key)
            if item is None:
                if requirement.required:
                    raise EntityError(f"Campo informativo obrigatório: {requirement.key}")
                continue
            field, upload = item
            if field.information_field_type != requirement.information_field_type:
                raise EntityError(f"Tipo inválido do campo informativo: {requirement.key}")
            if isinstance(field, FileInformationField):
                self._validate_file(requirement, field, upload)
            elif isinstance(field, TextInformationField) and requirement.required and not field.value.strip():
                raise EntityError(f"Campo informativo obrigatório: {requirement.key}")

    @staticmethod
    def _validate_file(requirement: TemplateInformationField, field: FileInformationField, upload) -> None:
        if field.source == FileSource.URL:
            # Hospedado por quem cria (ADR-0026): não há upload; a categoria já
            # veio do mimetype do link.
            if requirement.file_type is not None and field.file_type != requirement.file_type:
                raise EntityError(f"Tipo de arquivo inválido: {requirement.key}")
            return
        if upload is None:
            raise EntityError(f"Arquivo ausente: {requirement.key}")
        if requirement.file_type is None:
            return
        # A categoria vale pelo mimetype declarado; o `file_type` do corpo, se
        # vier, não pode contradizer a exigência.
        declared = FileType.IMAGE if upload.mimetype.lower().startswith("image/") else FileType.DOCUMENT
        if declared != requirement.file_type or (field.file_type and field.file_type != requirement.file_type):
            raise EntityError(f"Tipo de arquivo inválido: {requirement.key}")

    @staticmethod
    def _validate_version(version: int) -> int:
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise EntityError("Versão do template deve ser um inteiro a partir de 1")
        return version

    def bump_version(self) -> None:
        """Nova versão: o template já tem formulários e o conteúdo que eles
        copiam (seções, motivos) mudou. Os formulários existentes continuam na
        versão em que nasceram até alguém propagar a nova."""
        self.version += 1

    @staticmethod
    def _validate_id(id_to_validate: str) -> None:
        if not isinstance(id_to_validate, str) or len(id_to_validate) != Template.ID_LENGTH:
            raise EntityError("ID do template inválido ou ausente")

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str) or not name:
            raise EntityError("Nome do template deve ser uma string não vazia")

    @staticmethod
    def _validate_description(description: Optional[str]) -> None:
        if description is not None and (not isinstance(description, str) or description == ""):
            raise EntityError("Descrição deve ser uma string não vazia")

    @staticmethod
    def _validate_system(system: str) -> None:
        if not isinstance(system, str) or not system:
            raise EntityError("Sistema deve ser uma string não vazia")

    @staticmethod
    def _validate_is_active(is_active: bool) -> None:
        if not isinstance(is_active, bool):
            raise EntityError("Campo 'is_active' deve ser verdadeiro ou falso")

    @staticmethod
    def _validate_created_by(created_by: str) -> None:
        if not isinstance(created_by, str):
            raise EntityError("ID do criador deve ser uma string")

    @staticmethod
    def _validate_created_at(created_at: int) -> None:
        if not isinstance(created_at, int):
            raise EntityError("Timestamp de criação deve ser um inteiro")

    @staticmethod
    def _validate_updated_at(updated_at: int) -> None:
        if not isinstance(updated_at, int):
            raise EntityError("Timestamp de atualização deve ser um inteiro")

    @staticmethod
    def _validate_sections(sections: List[Section]) -> None:
        if not isinstance(sections, list) or not sections or not all(isinstance(section, Section) for section in sections):
            raise EntityError("Seções devem ser uma lista não vazia de seções válidas")

    @staticmethod
    def _validate_justification_options(options: Optional[List[JustificationOption]]) -> List[JustificationOption]:
        if options is None:
            return []
        if not isinstance(options, list) or not all(isinstance(option, JustificationOption) for option in options):
            raise EntityError("Motivos de cancelamento devem ser uma lista de opções válidas")
        labels = [option.option.strip() for option in options]
        if any(not label for label in labels):
            raise EntityError("Motivo de cancelamento não pode ser vazio")
        if len(set(labels)) != len(labels):
            raise EntityError("Motivos de cancelamento repetidos")
        return options

    def change_justification_options(self, options: List[JustificationOption]):
        self.justification_options = self._validate_justification_options(options)

    @staticmethod
    def validate_id(id_to_validate: str) -> bool:
        try:
            Template._validate_id(id_to_validate)
        except EntityError:
            return False
        return True

    def change_name(self, name: str):
        self._validate_name(name)
        self.name = name

    def change_description(self, description: Optional[str]):
        self._validate_description(description)
        self.description = description

    def change_system(self, system: str):
        self._validate_system(system)
        self.system = system

    def change_is_active(self, is_active: bool):
        self._validate_is_active(is_active)
        self.is_active = is_active

    def change_sections(self, sections: List[Section]):
        self._validate_sections(sections)
        self.sections = sections

    def change_updated_at(self, updated_at: int):
        self._validate_updated_at(updated_at)
        self.updated_at = updated_at
