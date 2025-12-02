from typing import List, Optional
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.helpers.errors.domain_errors import EntityError


class JustificationDTO:
    options: Optional[List[JustificationOption]]
    selected: Optional[SelectedJustification]

    def __init__(self, options: Optional[List[JustificationOption]], selected: Optional[SelectedJustification]):
        self.options = options
        self.selected = selected

    def from_request(justification_dict: dict) -> "JustificationDTO":
        options = None
        if justification_dict.get('options') is not None:
            if not justification_dict.get('options'):
                raise EntityError('options')
            options_data = justification_dict.get('options')

            options = []
            for option_data in options_data:
                if option_data.get('option') is None:
                    raise EntityError('option')

                if option_data.get('required_image') is None:
                    raise EntityError('required_image')

                if option_data.get('required_text') is None:
                    raise EntityError('required_text')

                option = JustificationOption(
                    option=option_data.get('option'),
                    required_image=option_data.get('required_image'),
                    required_text=option_data.get('required_text')
                )
                options.append(option)

        selected = None
        selected_dict = justification_dict.get('selected')
        if selected_dict is not None:
            if selected_dict.get('option') is None:
                raise EntityError('option')
            selected = SelectedJustification(
                option=selected_dict.get('option'),
                text=selected_dict.get('text'),
                image_url=selected_dict.get('image_url')
            )

        return JustificationDTO(options=options, selected=selected)

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
            } if self.selected is not None else None
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

        return JustificationDTO(options=options, selected=selected)

    def to_entity(self) -> Justification:
        return Justification(options=self.options, selected=self.selected)
