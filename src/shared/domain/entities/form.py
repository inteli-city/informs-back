import abc
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.file_upload import FileUploadRequest
from src.shared.domain.entities.information_field import InformationField
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
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
    priority: Priority
    observation: Optional[str]
    expiration_date: Optional[int]
    status: FormStatus
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
        priority: Priority,
        status: FormStatus,
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
            raise EntityError('Título do formulário deve ser uma string')
        self.form_title = form_title

        if not Form.validate_id(id):
            raise EntityError('ID do formulário inválido ou ausente')
        self.id = id

        if not Form.validate_id(user_id):
            raise EntityError('ID do usuário inválido ou ausente')
        self.user_id = user_id

        if not Form.validate_id(created_by):
            raise EntityError('ID do criador inválido ou ausente')
        self.created_by = created_by

        if template is not None and not isinstance(template, str):
            raise EntityError('ID do template deve ser uma string')
        self.template = template

        if area is not None and not isinstance(area, str):
            raise EntityError('Área deve ser uma string')
        self.area = area

        if not isinstance(system, str):
            raise EntityError('Sistema deve ser uma string')
        self.system = system

        if not isinstance(city, str):
            raise EntityError('Cidade deve ser uma string')
        self.city = city

        if not isinstance(street, str):
            raise EntityError('Rua deve ser uma string')
        self.street = street

        if number is not None and not isinstance(number, int):
            raise EntityError('Número deve ser um inteiro')
        self.number = number

        if not isinstance(latitude, (float, int)):
            raise EntityError('Latitude deve ser um número')
        if not -90 <= float(latitude) <= 90:
            raise EntityError('Latitude deve estar entre -90 e 90')
        self.latitude = float(latitude)

        if not isinstance(longitude, (float, int)):
            raise EntityError('Longitude deve ser um número')
        if not -180 <= float(longitude) <= 180:
            raise EntityError('Longitude deve estar entre -180 e 180')
        self.longitude = float(longitude)

        if not isinstance(priority, Priority):
            raise EntityError('Prioridade inválida')
        self.priority = priority

        if observation is not None and not isinstance(observation, str):
            raise EntityError('Observação deve ser uma string')
        self.observation = observation

        if expiration_date is not None and not isinstance(expiration_date, int):
            raise EntityError('Data de expiração deve ser um timestamp inteiro')
        self.expiration_date = expiration_date

        if not isinstance(status, FormStatus):
            raise EntityError('Status do formulário inválido')
        self.status = status

        if in_progress_at is not None and not isinstance(in_progress_at, int):
            raise EntityError('Timestamp de início deve ser um inteiro')
        self.in_progress_at = in_progress_at

        if cancelled_at is not None and not isinstance(cancelled_at, int):
            raise EntityError('Timestamp de cancelamento deve ser um inteiro')
        self.cancelled_at = cancelled_at

        if completed_at is not None and not isinstance(completed_at, int):
            raise EntityError('Timestamp de conclusão deve ser um inteiro')
        self.completed_at = completed_at

        if not isinstance(created_at, int):
            raise EntityError('Timestamp de criação deve ser um inteiro')
        self.created_at = created_at

        if not isinstance(updated_at, int):
            raise EntityError('Timestamp de atualização deve ser um inteiro')
        self.updated_at = updated_at

        if justification is None or not isinstance(justification, Justification):
            raise EntityError('Justificativa é obrigatória e deve ser válida')
        self.justification = justification

        template_is_uuid = Form._is_uuid_string(template) if template is not None else False
        if not isinstance(sections, list) or not all(isinstance(section, Section) for section in sections):
            raise EntityError('Seções devem ser uma lista de seções válidas')
        if not sections and not template_is_uuid:
            raise EntityError('Formulário sem template deve ter ao menos uma seção')
        self.sections = sections

        if information_fields is not None:
            if not isinstance(information_fields, list) or not all(isinstance(information_field, InformationField) for information_field in information_fields):
                raise EntityError('Campos informativos devem ser uma lista válida')
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
            raise EntityError('Timestamp de início deve ser um inteiro')
        if not isinstance(updated_at, int):
            raise EntityError('Timestamp de atualização deve ser um inteiro')

        if self.status != FormStatus.PENDING:
            raise ForbiddenAction("Formulário não está aberto para início")

        self.status = FormStatus.IN_PROGRESS
        self.in_progress_at = in_progress_at
        self.updated_at = updated_at

    def update_status(self, new_status: FormStatus, updated_at: int):
        if not isinstance(new_status, FormStatus):
            raise EntityError('Novo status inválido')
        if not isinstance(updated_at, int):
            raise EntityError('Timestamp de atualização deve ser um inteiro')

        if new_status in [FormStatus.CANCELLED, FormStatus.COMPLETED]:
            raise ForbiddenAction("Não é possível alterar o status para cancelado ou concluído")

        if self.status in [FormStatus.CANCELLED, FormStatus.COMPLETED]:
            raise ForbiddenAction("Formulário já finalizado")

        if new_status == self.status:
            raise DuplicatedItem("O status do formulário já é o mesmo que o informado")

        if new_status is FormStatus.PENDING and self.status is FormStatus.IN_PROGRESS:
            self.in_progress_at = None
        elif new_status is FormStatus.IN_PROGRESS:
            self.in_progress_at = updated_at

        self.status = new_status
        self.updated_at = updated_at

    def ensure_assigned_to(self, user_id: str, message: str):
        if self.user_id != user_id:
            raise ForbiddenAction(message)

    def is_finished(self) -> bool:
        return self.status in [FormStatus.CANCELLED, FormStatus.COMPLETED]

    def ensure_in_progress(self):
        if self.status is not FormStatus.IN_PROGRESS:
            raise ForbiddenAction("Formulário não está em andamento")

    def _find_section(self, section_id: int, section_instance: int = 0) -> Section:
        section = next(
            (s for s in self.sections if s.section_id == section_id and s.section_instance == section_instance),
            None,
        )
        if section is None:
            raise EntityError(f"Seção {section_id} (instância {section_instance}) não encontrada no formulário")
        return section

    @staticmethod
    def _find_field_index(section: Section, field_key: str) -> int:
        field_index = next((idx for idx, field in enumerate(section.fields) if field.key == field_key), None)
        if field_index is None:
            raise EntityError(f"Campo '{field_key}' não encontrado na seção {section.section_id}")
        return field_index

    @staticmethod
    def _normalize_file_uploads(value) -> Tuple[List[FileUploadRequest], List[dict]]:
        uploads_raw = value
        if isinstance(uploads_raw, dict):
            uploads_raw = [uploads_raw]
        if not isinstance(uploads_raw, list) or not uploads_raw:
            raise EntityError("Valor do campo de arquivo deve ser uma lista não vazia de objetos com 'filename' e 'mimetype'")

        normalized_uploads = []
        normalized_value = []
        for upload in uploads_raw:
            if isinstance(upload, FileUploadRequest):
                normalized_uploads.append(upload)
                normalized_value.append(upload.to_dict())
                continue
            if not isinstance(upload, dict):
                raise EntityError("Cada arquivo deve ser um objeto com 'filename' e 'mimetype'")
            filename = upload.get("filename")
            mimetype = upload.get("mimetype")
            if filename is None or mimetype is None:
                raise EntityError("Cada arquivo deve conter 'filename' e 'mimetype'")
            if not isinstance(filename, str) or not isinstance(mimetype, str):
                raise EntityError("'filename' e 'mimetype' devem ser strings")
            file_upload = FileUploadRequest(filename=filename, mimetype=mimetype)
            normalized_uploads.append(file_upload)
            normalized_value.append(file_upload.to_dict())
        return normalized_uploads, normalized_value

    def apply_field_values(self, fields: List[dict]) -> Dict[Tuple[int, int, str], List[FileUploadRequest]]:
        import copy

        if not isinstance(fields, list):
            raise EntityError("Campos devem ser uma lista")

        base_sections = {
            s.section_id: copy.deepcopy(s)
            for s in self.sections if s.section_instance == 0
        }

        seen = set()
        file_uploads = {}
        for item in fields:
            if not isinstance(item, dict):
                raise EntityError("Campo deve ser um objeto")
            section_id = item.get("section_id")
            section_instance = item.get("section_instance", 0)
            field_key = item.get("field_key")
            value = item.get("value")

            key = (section_id, section_instance, field_key)
            if key in seen:
                raise EntityError(f"Campo '{field_key}' duplicado na seção {section_id} instância {section_instance}")
            seen.add(key)

            if section_instance != 0:
                exists = any(
                    s.section_id == section_id and s.section_instance == section_instance
                    for s in self.sections
                )
                if not exists:
                    base = base_sections.get(section_id)
                    if base is None:
                        raise EntityError(f"Seção {section_id} não encontrada no formulário")
                    if not base.is_duplicable:
                        raise EntityError(f"Seção {section_id} não é duplicável")
                    new_section = copy.deepcopy(base)
                    new_section.section_instance = section_instance
                    self.sections.append(new_section)

            section = self._find_section(section_id, section_instance)
            field_index = self._find_field_index(section, field_key)
            existing_field = section.fields[field_index]

            if isinstance(existing_field, FileField) and value is not None:
                uploads, value = self._normalize_file_uploads(value)
                file_uploads[key] = uploads

            section.fields[field_index] = existing_field.with_value(value)

        self.ensure_required_fields_filled()
        return file_uploads

    def set_file_field_urls(self, section_id: int, field_key: str, file_urls: List[str], section_instance: int = 0):
        if not isinstance(file_urls, list) or not file_urls or not all(isinstance(url, str) for url in file_urls):
            raise EntityError("URLs de arquivo devem ser uma lista não vazia")
        section = self._find_section(section_id, section_instance)
        field_index = self._find_field_index(section, field_key)
        field = section.fields[field_index]
        if not isinstance(field, FileField):
            raise EntityError("Campo não é do tipo arquivo")
        field.set_value(file_urls)

    def ensure_required_fields_filled(self):
        for section in self.sections:
            for field in section.fields:
                if field.required and field.value is None:
                    raise EntityError("Campo obrigatório não preenchido")

    def complete(self, completed_at: int, updated_at: int):
        if not isinstance(completed_at, int):
            raise EntityError('Timestamp de conclusão deve ser um inteiro')
        if not isinstance(updated_at, int):
            raise EntityError('Timestamp de atualização deve ser um inteiro')
        if self.status is not FormStatus.IN_PROGRESS:
            raise ForbiddenAction("Formulário não está em andamento")

        self.ensure_required_fields_filled()
        self.status = FormStatus.COMPLETED
        self.completed_at = completed_at
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
            raise EntityError('Timestamp de cancelamento deve ser um inteiro')
        if not isinstance(updated_at, int):
            raise EntityError('Timestamp de atualização deve ser um inteiro')

        if self.is_finished():
            raise ForbiddenAction("Formulário já está finalizado e não pode ser cancelado")

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

        self.status = FormStatus.CANCELLED
        self.cancelled_at = cancelled_at
        self.updated_at = updated_at
