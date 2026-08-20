import abc
from typing import List, Optional

from src.shared.helpers.errors.domain_errors import EntityError


class JustificationOption(abc.ABC):
    option: str
    required_image: bool
    required_text: bool

    def __init__(self, option: str, required_image: bool, required_text: bool):
        if not isinstance(option, str):
            raise EntityError('Opção de justificativa deve ser uma string')
        self.option = option

        if not isinstance(required_image, bool):
            raise EntityError("Campo 'required_image' deve ser verdadeiro ou falso")
        self.required_image = required_image

        if not isinstance(required_text, bool):
            raise EntityError("Campo 'required_text' deve ser verdadeiro ou falso")
        self.required_text = required_text


class SelectedJustification(abc.ABC):
    option: str
    text: Optional[str]
    image_url: Optional[str]
    image_integrity: Optional[dict]

    def __init__(self, option: str, text: Optional[str] = None, image_url: Optional[str] = None, image_integrity: Optional[dict] = None):
        if not isinstance(option, str):
            raise EntityError('Opção selecionada deve ser uma string')
        self.option = option

        if text is not None and not isinstance(text, str):
            raise EntityError('Texto da justificativa deve ser uma string')
        self.text = text

        if image_url is not None and not isinstance(image_url, str):
            raise EntityError('URL da imagem de justificativa deve ser uma string')
        self.image_url = image_url
        if image_integrity is not None and not isinstance(image_integrity, dict):
            raise EntityError('Metadados da imagem de justificativa devem ser um objeto')
        self.image_integrity = image_integrity


class Justification(abc.ABC):
    options: List[JustificationOption]
    selected: Optional[SelectedJustification]

    def __init__(self, options: List[JustificationOption], selected: Optional[SelectedJustification] = None, selected_option: Optional[str] = None, justification_text: Optional[str] = None, justification_image: Optional[str] = None, justification_image_integrity: Optional[dict] = None):
        if not isinstance(options, list) or not options or not all(isinstance(option, JustificationOption) for option in options):
            raise EntityError('Opções de justificativa devem ser uma lista não vazia válida')
        self.options = options

        selected_payload = selected
        if selected_payload is None and selected_option is not None:
            selected_payload = SelectedJustification(option=selected_option, text=justification_text, image_url=justification_image, image_integrity=justification_image_integrity)

        if selected_payload is not None and not isinstance(selected_payload, SelectedJustification):
            raise EntityError('Justificativa selecionada deve ser um objeto SelectedJustification válido')

        if selected_payload is not None:
            matched_option = next((option for option in options if option.option == selected_payload.option), None)
            if matched_option is None:
                raise EntityError(f"Opção selecionada '{selected_payload.option}' não está entre as opções disponíveis")
        self.selected = selected_payload
        self.selected_option = selected_payload.option if selected_payload else None  # compatibility
        self.justification_text = selected_payload.text if selected_payload else None  # compatibility
        self.justification_image = selected_payload.image_url if selected_payload else None  # compatibility
        self.justification_image_integrity = selected_payload.image_integrity if selected_payload else None  # compatibility
