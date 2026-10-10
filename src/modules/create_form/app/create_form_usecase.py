from copy import deepcopy
from typing import List, Optional
import uuid

from src.shared.domain.entities.app_config import AppConfig
from src.shared.domain.entities.file_upload import FileUpload, FileUploadRequest
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import FileInformationField, InformationField
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.form_origin_enum import FormOrigin
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms, utc_year
from src.shared.helpers.functions.s3_url import build_s3_url


class CreateFormUsecase:
    def __init__(
        self,
        form_repo: IFormRepository,
        file_repo: IFileRepository,
        template_repo: Optional[ITemplateRepository] = None,
        system_config_repo: Optional[ISystemConfigRepository] = None,
        access_control: Optional[AccessControl] = None,
    ):
        self.form_repo = form_repo
        self.file_repo = file_repo
        self.template_repo = template_repo
        self.system_config_repo = system_config_repo
        self.access_control = access_control

    def _allows_unassigned_forms(self, system: str) -> bool:
        if self.system_config_repo is None:
            return False
        config = self.system_config_repo.get_by_system(system)
        return bool(config and config.allow_unassigned_forms)

    def _ensure_app_config_allows_creation(self, system: str, user_id: Optional[str], created_by: str) -> None:
        """
        O que a configuração da aplicação esconde no app também é recusado
        aqui — esconder o botão não impede quem chama a API direto.

        Quem administra o sistema (role ADMIN nele, ou super admin) não passa
        por esta regra: é como as integrações criam as OS do pool em sistemas
        onde o menu Criar fica desligado para quem está em campo.
        """
        if self.system_config_repo is None or self.access_control is None:
            return
        if self.access_control.is_system_admin(created_by, system):
            return

        system_config = self.system_config_repo.get_by_system(system)
        default = self.system_config_repo.get_default_app_config()
        config = AppConfig.effective(
            default.values if default else None,
            system_config.app_config if system_config else None,
            bool(system_config and system_config.allow_unassigned_forms),
        )
        if not config.menus.create_form:
            raise ForbiddenAction("Criação de formulário não está habilitada para este sistema")
        if user_id is None and not config.creation.allow_open:
            raise ForbiddenAction("Criação de formulário em aberto não está habilitada para este sistema")

    def __call__(
        self,
        form_title: str,
        created_by: str,
        user_id: Optional[str],
        system: str,
        street: str,
        city: str,
        latitude: float,
        longitude: float,
        priority: Priority,
        sections: List[Section],
        justification: Justification,
        template: Optional[str] = None,
        number: Optional[int] = None,
        observation: Optional[str] = None,
        expiration_date: Optional[int] = None,
        information_fields: Optional[List[InformationField]] = None,
        information_fields_uploads: Optional[List[Optional[FileUploadRequest]]] = None,
        requester_systems: Optional[List[str]] = None,
        external_id: Optional[str] = None,
        origin: Optional[FormOrigin] = None,
        service_type: Optional[str] = None,
        occurred_at: Optional[int] = None,
        scheduled_start_at: Optional[int] = None,
        scheduled_end_at: Optional[int] = None,
        attributes: Optional[dict] = None,
    ) -> tuple[Form, list[FileUpload]]:
        if requester_systems is not None and system not in requester_systems:
            raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")

        if external_id is not None:
            existing_form = self.form_repo.get_form_by_external_id(system, external_id)
            if existing_form is not None:
                return existing_form, []

        self._ensure_app_config_allows_creation(system, user_id, created_by)

        if user_id is None and not self._allows_unassigned_forms(system):
            raise MissingParameters("user_id")

        form_id = str(uuid.uuid4())
        now_timestamp = now_timestamp_ms()

        template_entity = self._load_template(template, system)
        resolved_sections = deepcopy(template_entity.sections) if template_entity else sections
        justification = self._inherit_justification(justification, template_entity)
        files = self._process_information_field_uploads(
            information_fields, information_fields_uploads, system, form_id
        )

        form = Form(
            form_title=form_title,
            id=form_id,
            created_by=created_by,
            user_id=user_id,
            template=template,
            system=system,
            street=street,
            city=city,
            number=number,
            latitude=latitude,
            longitude=longitude,
            priority=priority,
            status=FormStatus.PENDING,
            created_at=now_timestamp,
            updated_at=now_timestamp,
            sections=resolved_sections,
            observation=observation,
            expiration_date=expiration_date,
            justification=justification,
            information_fields=information_fields,
            external_id=external_id,
            origin=origin,
            service_type=service_type,
            occurred_at=occurred_at,
            scheduled_start_at=scheduled_start_at,
            scheduled_end_at=scheduled_end_at,
            attributes=attributes,
        )

        created_form = self.form_repo.create_form(form)
        return created_form, files

    @staticmethod
    def _inherit_justification(justification: Justification, template_entity) -> Justification:
        """Sem motivos de cancelamento próprios (o app manda um placeholder com
        opção em branco), o formulário herda os do template."""
        own = [option for option in justification.options if option.option.strip()]
        if own or template_entity is None or not template_entity.justification_options:
            return justification
        return Justification(options=deepcopy(template_entity.justification_options))

    def _load_template(self, template: Optional[str], system: str):
        if template is None:
            return None
        if self.template_repo is None:
            raise EntityError("template")
        resolved_template = self.template_repo.get_template(template)
        if resolved_template is None:
            raise NoItemsFound("Template não encontrado")
        if resolved_template.system != system:
            raise ForbiddenAction("Template não pertence ao sistema informado")
        if not resolved_template.is_active:
            raise ForbiddenAction("Template não está ativo")
        return resolved_template

    def _process_information_field_uploads(
        self,
        information_fields: Optional[List[InformationField]],
        information_fields_uploads: Optional[List[Optional[FileUploadRequest]]],
        system: str,
        form_id: str,
    ) -> list[FileUpload]:
        files: list[FileUpload] = []
        if not information_fields:
            return files
        uploads = information_fields_uploads or []
        for idx, information_field in enumerate(information_fields):
            if not isinstance(information_field, FileInformationField):
                continue
            upload = uploads[idx] if idx < len(uploads) else None
            if not isinstance(upload, FileUploadRequest):
                raise EntityError("mimetype")
            files.append(self._prepare_file_information_field(information_field, upload, system, form_id))
        return files

    def _prepare_file_information_field(
        self,
        information_field: FileInformationField,
        upload: FileUploadRequest,
        system: str,
        form_id: str,
    ) -> FileUpload:
        mimetype = upload.mimetype
        file_path = f'{utc_year()}/{system}/{form_id}/information_field/{str(uuid.uuid4())}.{mimetype.split("/")[-1]}'
        presigned_url = self.file_repo.generate_presigned_url(file_path=file_path, mimetype=mimetype)
        file_url = build_s3_url(file_path)
        information_field.file_path = file_url
        if information_field.file_type is None:
            information_field.file_type = FileType.IMAGE if mimetype.lower().startswith("image/") else FileType.DOCUMENT
        return FileUpload(
            filename=upload.filename,
            mimetype=mimetype,
            pre_signed_url=presigned_url,
            file_path=file_path,
            file_url=file_url,
            section_id=None,
            field_key=None,
            file_index=None,
        )
