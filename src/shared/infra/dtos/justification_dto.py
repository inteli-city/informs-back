from typing import List, Optional
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.helpers.errors.domain_errors import EntityError


class JustificationDTO:
    options: Optional[List[JustificationOption]]
    selected: Optional[SelectedJustification]
    selected_option: Optional[str]
    justification_text: Optional[str]
    justification_image: Optional[str]

    def __init__(self, options: Optional[List[JustificationOption]], selected: Optional[SelectedJustification] = None, selected_option: Optional[str] = None, justification_text: Optional[str] = None, justification_image: Optional[str] = None):
        self.options = options
        if selected is None and selected_option is not None:
            selected = SelectedJustification(option=selected_option, text=justification_text, image_url=justification_image)
        self.selected = selected
        self.selected_option = self.selected.option if self.selected else None
        self.justification_text = self.selected.text if self.selected else None
        self.justification_image = self.selected.image_url if self.selected else None

    @staticmethod
    def from_request(justification_dict: dict) -> "JustificationDTO":
        options_data = justification_dict.get('options')
        if not options_data:
            raise EntityError('options')

        options = [JustificationDTO._parse_option(option_data) for option_data in options_data]
        selected = JustificationDTO._parse_selected(justification_dict)
        return JustificationDTO(options=options, selected=selected)

    @staticmethod
    def _parse_option(option_data: dict) -> JustificationOption:
        for key in ('option', 'required_image', 'required_text'):
            if option_data.get(key) is None:
                raise EntityError(key)
        return JustificationOption(
            option=option_data.get('option'),
            required_image=option_data.get('required_image'),
            required_text=option_data.get('required_text')
        )

    @staticmethod
    def _parse_selected(justification_dict: dict) -> Optional[SelectedJustification]:
        selected_dict = justification_dict.get('selected') or {}
        if not selected_dict and justification_dict.get('selected_option') is not None:
            selected_dict = {
                "option": justification_dict.get('selected_option'),
                "text": justification_dict.get('justification_text'),
                "image_url": justification_dict.get('justification_image')
            }

        if not selected_dict:
            return None

        if selected_dict.get('option') is None:
            raise EntityError('option')
        return SelectedJustification(
            option=selected_dict.get('option'),
            text=selected_dict.get('text'),
            image_url=selected_dict.get('image_url')
        )

    @staticmethod
    def from_entity(justification: Justification) -> "JustificationDTO":
        return JustificationDTO(options=justification.options, selected=justification.selected)
    
    def to_dynamo(self) -> dict:
        return {
            "options": [{
                "option": option.option,
                "required_image": option.required_image,
                "required_text": option.required_text
            } for option in self.options] if self.options is not None else None,
            "selected": {
                "option": self.selected.option,
                "text": self.selected.text,
                "image_url": self.selected.image_url
            } if self.selected is not None else None,
            "selected_option": self.selected.option if self.selected else None,
            "justification_text": self.selected.text if self.selected else None,
            "justification_image": self.selected.image_url if self.selected else None
        }

    @staticmethod
    def from_dynamo(justification_dict: dict) -> "JustificationDTO":
        options_data = justification_dict.get('options')
        options = None
        if options_data is not None:
            options = [JustificationOption(**option_data) for option_data in options_data]

        selected_dict = justification_dict.get('selected')
        selected = None
        if selected_dict is not None:
            selected = SelectedJustification(
                option=selected_dict.get('option'),
                text=selected_dict.get('text'),
                image_url=selected_dict.get('image_url')
            )

        selected_option = justification_dict.get('selected_option') if selected is None else None
        justification_text = justification_dict.get('justification_text') if selected is None else None
        justification_image = justification_dict.get('justification_image') if selected is None else None

        return JustificationDTO(options=options, selected=selected, selected_option=selected_option, justification_text=justification_text, justification_image=justification_image)

    def to_entity(self) -> Justification:
        return Justification(options=self.options, selected=self.selected)
