import abc
from typing import List, Optional

from src.shared.domain.entities.information_field import InformationField
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.helpers.errors.domain_errors import EntityError


class Form(abc.ABC):
    form_title: str
    id: str
    user_id: str
    created_by: str
    template: Optional[str]
    system: str
    city: str
    area: Optional[str]
    street: str
    number: Optional[int]
    latitude: float
    longitude: float
    priority: PRIORITY
    observation: Optional[str]
    expiration_date: Optional[int]
    status: FORM_STATUS
    in_progress_at: Optional[int]
    cancelled_at: Optional[int]
    completed_at: Optional[int]
    created_at: int
    updated_at: int
    sections: List[Section]
    justification: Optional[Justification]
    information_fields: Optional[List[InformationField]]

    ID_LENGTH = 36

    def __init__(
        self,
        id: str,
        form_title: str,
        user_id: str,
        created_by: str,
        system: str,
        city: str,
        street: str,
        latitude: float,
        longitude: float,
        priority: PRIORITY,
        status: FORM_STATUS,
        created_at: int,
        updated_at: int,
        sections: List[Section],
        template: Optional[str] = None,
        area: Optional[str] = None,
        number: Optional[int] = None,
        observation: Optional[str] = None,
        expiration_date: Optional[int] = None,
        in_progress_at: Optional[int] = None,
        cancelled_at: Optional[int] = None,
        completed_at: Optional[int] = None,
        justification: Optional[Justification] = None,
        information_fields: Optional[List[InformationField]] = None,
    ):

        if not isinstance(form_title, str):
            raise EntityError('form_title')
        self.form_title = form_title

        if not Form.validate_id(id):
            raise EntityError('id')
        self.id = id
        self.form_id = id  # compat

        if not Form.validate_id(user_id):
            raise EntityError('user_id')
        self.user_id = user_id

        if not Form.validate_id(created_by):
            raise EntityError('created_by')
        self.created_by = created_by
        self.creator_user_id = created_by  # compat

        if template is not None and not isinstance(template, str):
            raise EntityError('template')
        self.template = template

        if area is not None and not isinstance(area, str):
            raise EntityError('area')
        self.area = area

        if not isinstance(system, str):
            raise EntityError('system')
        self.system = system

        if not isinstance(city, str):
            raise EntityError('city')
        self.city = city

        if not isinstance(street, str):
            raise EntityError('street')
        self.street = street

        if number is not None and not isinstance(number, int):
            raise EntityError('number')
        self.number = number

        if not isinstance(latitude, (float, int)):
            raise EntityError('latitude')
        self.latitude = float(latitude)

        if not isinstance(longitude, (float, int)):
            raise EntityError('longitude')
        self.longitude = float(longitude)

        if not isinstance(priority, PRIORITY):
            raise EntityError('priority')
        self.priority = priority

        if observation is not None and not isinstance(observation, str):
            raise EntityError('observation')
        self.observation = observation

        if expiration_date is not None and not isinstance(expiration_date, int):
            raise EntityError('expiration_date')
        self.expiration_date = expiration_date

        if not isinstance(status, FORM_STATUS):
            raise EntityError('status')
        self.status = status

        if in_progress_at is not None and not isinstance(in_progress_at, int):
            raise EntityError('in_progress_at')
        self.in_progress_at = in_progress_at
        self.start_date = in_progress_at  # compat

        if cancelled_at is not None and not isinstance(cancelled_at, int):
            raise EntityError('cancelled_at')
        self.cancelled_at = cancelled_at

        if completed_at is not None and not isinstance(completed_at, int):
            raise EntityError('completed_at')
        self.completed_at = completed_at
        self.conclusion_date = completed_at  # compat

        if not isinstance(created_at, int):
            raise EntityError('created_at')
        self.created_at = created_at
        self.creation_date = created_at  # compat

        if not isinstance(updated_at, int):
            raise EntityError('updated_at')
        self.updated_at = updated_at

        if justification is not None and not isinstance(justification, Justification):
            raise EntityError('justification')
        self.justification = justification

        if not isinstance(sections, list) or not sections or not all(isinstance(section, Section) for section in sections):
            raise EntityError('sections')
        self.sections = sections

        if information_fields is not None:
            if not isinstance(information_fields, list) or not information_fields or not all(isinstance(information_field, InformationField) for information_field in information_fields):
                raise EntityError('information_fields')
        self.information_fields = information_fields

    @staticmethod
    def validate_id(id_to_validate: str) -> bool:
        if not isinstance(id_to_validate, str):
            return False
        if len(id_to_validate) != Form.ID_LENGTH:
            return False
        return True
