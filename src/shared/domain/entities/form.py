import abc
from typing import List, Optional
from uuid import UUID

from src.shared.domain.entities.information_field import InformationField
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction


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
    justification: Justification
    information_fields: Optional[List[InformationField]]

    ID_LENGTH = 36

    @staticmethod
    def _is_uuid_string(value: str) -> bool:
        if not isinstance(value, str):
            return False
        try:
            UUID(value)
            return True
        except (ValueError, TypeError, AttributeError):
            return False

    def __init__(
        self,
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
        id: Optional[str] = None,
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

        if not Form.validate_id(user_id):
            raise EntityError('user_id')
        self.user_id = user_id

        if not Form.validate_id(created_by):
            raise EntityError('created_by')
        self.created_by = created_by

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

        if cancelled_at is not None and not isinstance(cancelled_at, int):
            raise EntityError('cancelled_at')
        self.cancelled_at = cancelled_at

        if completed_at is not None and not isinstance(completed_at, int):
            raise EntityError('completed_at')
        self.completed_at = completed_at

        if not isinstance(created_at, int):
            raise EntityError('created_at')
        self.created_at = created_at

        if not isinstance(updated_at, int):
            raise EntityError('updated_at')
        self.updated_at = updated_at

        if justification is None or not isinstance(justification, Justification):
            raise EntityError('justification')
        self.justification = justification

        template_is_uuid = Form._is_uuid_string(template) if template is not None else False
        if not isinstance(sections, list) or not all(isinstance(section, Section) for section in sections):
            raise EntityError('sections')
        if not sections and not template_is_uuid:
            raise EntityError('sections')
        self.sections = sections

        if information_fields is not None:
            if not isinstance(information_fields, list) or not all(isinstance(information_field, InformationField) for information_field in information_fields):
                raise EntityError('information_fields')
        self.information_fields = information_fields

    @staticmethod
    def validate_id(id_to_validate: str) -> bool:
        if not isinstance(id_to_validate, str):
            return False
        if len(id_to_validate) != Form.ID_LENGTH:
            return False
        return True

    def start(self, in_progress_at: int, updated_at: int):
        if not isinstance(in_progress_at, int):
            raise EntityError('in_progress_at')
        if not isinstance(updated_at, int):
            raise EntityError('updated_at')

        if self.status != FORM_STATUS.PENDING:
            raise ForbiddenAction("Formulário não está aberto para início")

        self.status = FORM_STATUS.IN_PROGRESS
        self.in_progress_at = in_progress_at
        self.updated_at = updated_at

    def update_status(self, new_status: FORM_STATUS, updated_at: int):
        if not isinstance(new_status, FORM_STATUS):
            raise EntityError('status')
        if not isinstance(updated_at, int):
            raise EntityError('updated_at')

        if new_status in [FORM_STATUS.CANCELLED, FORM_STATUS.COMPLETED]:
            raise ForbiddenAction("Não é possível alterar o status para cancelado ou concluído")

        if self.status in [FORM_STATUS.CANCELLED, FORM_STATUS.COMPLETED]:
            raise ForbiddenAction("Formulário já finalizado")

        if new_status == self.status:
            raise DuplicatedItem("O status do formulário já é o mesmo que o informado")

        if new_status is FORM_STATUS.PENDING and self.status is FORM_STATUS.IN_PROGRESS:
            self.in_progress_at = None
        elif new_status is FORM_STATUS.IN_PROGRESS:
            self.in_progress_at = updated_at

        self.status = new_status
        self.updated_at = updated_at

    def cancel(
        self,
        selected_option: str,
        justification_text: Optional[str],
        justification_image: Optional[str],
        cancelled_at: int,
        updated_at: int,
    ):
        if not isinstance(cancelled_at, int):
            raise EntityError('cancelled_at')
        if not isinstance(updated_at, int):
            raise EntityError('updated_at')

        option = next((item for item in self.justification.options if item.option == selected_option), None)
        if option is None:
            raise EntityError("Opção de justificativa inválida")

        if option.required_text and not justification_text:
            raise EntityError("Justificativa de texto obrigatória")
        if option.required_image and not justification_image:
            raise EntityError("Justificativa de imagem obrigatória")

        self.justification = Justification(
            options=self.justification.options,
            selected_option=selected_option,
            justification_text=justification_text,
            justification_image=justification_image
        )

        self.status = FORM_STATUS.CANCELLED
        self.cancelled_at = cancelled_at
        self.updated_at = updated_at
