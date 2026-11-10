from typing import Optional

from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.information_field_type_enum import InformationFieldType
from src.shared.helpers.errors.domain_errors import EntityError


class TemplateInformationField:
    """Exigência que o template faz a quem cria o formulário: qual informação
    (`key`), de que tipo, se é obrigatória e, para arquivo, a categoria aceita.

    Não é o valor enviado (isso é `InformationField`): é a regra contra a qual
    o valor é conferido na criação do formulário."""

    key: str
    label: str
    information_field_type: InformationFieldType
    required: bool
    file_type: Optional[FileType]

    def __init__(
        self,
        key: str,
        label: str,
        information_field_type: InformationFieldType,
        required: bool = False,
        file_type: Optional[FileType] = None,
    ):
        if not isinstance(key, str) or not key.strip():
            raise EntityError("Chave do campo informativo deve ser uma string não vazia")
        if not isinstance(label, str) or not label.strip():
            raise EntityError("Rótulo do campo informativo deve ser uma string não vazia")
        if not isinstance(information_field_type, InformationFieldType):
            raise EntityError("Tipo de campo informativo inválido")
        if not isinstance(required, bool):
            raise EntityError("Obrigatoriedade do campo informativo deve ser booleana")
        if file_type is not None:
            if not isinstance(file_type, FileType):
                raise EntityError("Tipo de arquivo inválido")
            # Categoria de arquivo num campo de texto/mapa/URL nunca seria conferida.
            if information_field_type != InformationFieldType.FILE_INFORMATION_FIELD:
                raise EntityError("file_type é exclusivo de campos de arquivo")
        self.key = key
        self.label = label
        self.information_field_type = information_field_type
        self.required = required
        self.file_type = file_type

    def to_dict(self) -> dict:
        data = {
            "key": self.key,
            "label": self.label,
            "information_field_type": self.information_field_type.value,
            "required": self.required,
        }
        if self.file_type is not None:
            data["file_type"] = self.file_type.value
        return data

    @staticmethod
    def from_dict(data: dict) -> "TemplateInformationField":
        file_type = data.get("file_type")
        return TemplateInformationField(
            key=data.get("key"),
            label=data.get("label"),
            information_field_type=InformationFieldType(data["information_field_type"]),
            required=data.get("required", False),
            file_type=FileType(file_type) if file_type is not None else None,
        )

    def __eq__(self, other) -> bool:
        return isinstance(other, TemplateInformationField) and self.to_dict() == other.to_dict()

    def __hash__(self) -> int:
        return hash(self.key)
