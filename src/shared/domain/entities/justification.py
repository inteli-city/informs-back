import abc
from typing import List, Optional

from src.shared.helpers.errors.domain_errors import EntityError


class JustificationOption(abc.ABC):
    option: str
    required_image: bool
    required_text: bool

    def __init__(self, option: str, required_image: bool, required_text: bool):
        if not isinstance(option, str):
            raise EntityError('option')
        self.option = option

        if not isinstance(required_image, bool):
            raise EntityError('required_image')
        self.required_image = required_image

        if not isinstance(required_text, bool):
            raise EntityError('required_text')
        self.required_text = required_text


class SelectedJustification(abc.ABC):
    option: str
    text: Optional[str]
    image_url: Optional[str]

    def __init__(self, option: str, text: Optional[str] = None, image_url: Optional[str] = None):
        if not isinstance(option, str):
            raise EntityError('option')
        self.option = option

        if text is not None and not isinstance(text, str):
            raise EntityError('text')
        self.text = text

        if image_url is not None and not isinstance(image_url, str):
            raise EntityError('image_url')
        self.image_url = image_url


class Justification(abc.ABC):
    options: Optional[List[JustificationOption]]
    selected: Optional[SelectedJustification]

    def __init__(self, options: Optional[List[JustificationOption]], selected: Optional[SelectedJustification] = None):
        if options is not None:
            if not isinstance(options, list) or not all(isinstance(option, JustificationOption) for option in options):
                raise EntityError('options')
        self.options = options

        if selected is not None and not isinstance(selected, SelectedJustification):
            raise EntityError('selected')

        if selected is not None and options is not None:
            matched_option = next((option for option in options if option.option == selected.option), None)
            if matched_option is None:
                raise EntityError('selected')
            if matched_option.required_text and not selected.text:
                raise EntityError('text')
            if matched_option.required_image and not selected.image_url:
                raise EntityError('image_url')

        self.selected = selected
