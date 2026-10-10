import os
import sys
from copy import deepcopy

import pytest

sys.path.append(os.getcwd())

from src.modules.create_form.app.create_form_usecase import CreateFormUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.information_field import FileInformationField, TextInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.entities.file_upload import FileUploadRequest
from src.shared.domain.enums.form_origin_enum import FormOrigin
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.system_config_repository_mock import SystemConfigRepositoryMock
from src.shared.infra.repositories.system_role_repository_mock import SystemRoleRepositoryMock
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


def _make_usecase_and_payload():
    repo = FormRepositoryMock()
    file_repo = FileRepositoryMock()
    template_repo = TemplateRepositoryMock()
    usecase = CreateFormUsecase(repo, file_repo, template_repo)

    text_field = TextField(
        placeholder='placeholder',
        required=True,
        key='key',
        regex='regex',
        formatting='formatting',
        max_length=10,
        value='value',
    )
    section = Section(section_id=1, fields=[text_field])
    justification = Justification(
        options=[JustificationOption(option='option', required_image=True, required_text=True)]
    )

    payload = {
        "form_title": 'FORM TITLE',
        "created_by": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
        "user_id": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
        "system": 'GAIA',
        "street": '1',
        "city": '1',
        "latitude": 1.0,
        "longitude": 1.0,
        "priority": Priority.EMERGENCY,
        "sections": [section],
        "justification": justification,
        "information_fields": [TextInformationField(value='info')],
        "observation": 'obs',
        "expiration_date": 946407600000,
    }

    return usecase, payload, template_repo


class TestCreateFormUsecase:
    def test_create_form_usecase(self):
        usecase, payload, _ = _make_usecase_and_payload()

        form, files = usecase(**payload)

        assert len(form.id) == 36
        assert form.status == FormStatus.PENDING
        assert form.priority == Priority.EMERGENCY
        assert form.observation == 'obs'
        assert form.expiration_date == 946407600000
        assert form.sections[0].section_id == 1
        assert isinstance(form.information_fields[0], TextInformationField)
        assert files == []

    def test_create_form_usecase_with_files(self):
        usecase, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload["information_fields"] = [FileInformationField(file_path="")]
        payload["information_fields_uploads"] = [FileUploadRequest(filename="a.jpg", mimetype="image/jpeg")]

        form, files = usecase(**payload)

        assert form.information_fields[0].file_path.startswith("https://")
        assert len(files) == 1
        assert files[0].filename == "a.jpg"
        assert files[0].mimetype == "image/jpeg"

    def test_create_form_usecase_without_information_fields(self):
        usecase, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload.pop("information_fields")

        form, files = usecase(**payload)

        assert form.information_fields is None
        assert files == []

    def test_create_form_usecase_with_template_copies_sections(self):
        usecase, payload, template_repo = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload["template"] = template_repo.templates[0].id
        payload["sections"] = []

        form, files = usecase(**payload)

        assert form.template == template_repo.templates[0].id
        assert len(form.sections) == len(template_repo.templates[0].sections)
        assert form.sections[0].section_id == template_repo.templates[0].sections[0].section_id
        assert files == []

    def test_form_without_own_reasons_inherits_template_reasons(self):
        usecase, payload, template_repo = _make_usecase_and_payload()
        template = template_repo.templates[0]
        template.justification_options = [JustificationOption(option="Local inacessível", required_image=True, required_text=False)]
        payload = deepcopy(payload)
        payload["template"] = template.id
        payload["sections"] = []
        # O app manda um placeholder com opção em branco quando não tem motivos.
        payload["justification"] = Justification(options=[JustificationOption(option="", required_image=False, required_text=False)])

        form, _ = usecase(**payload)

        assert [option.option for option in form.justification.options] == ["Local inacessível"]

    def test_form_with_own_reasons_keeps_them(self):
        usecase, payload, template_repo = _make_usecase_and_payload()
        template = template_repo.templates[0]
        template.justification_options = [JustificationOption(option="Do template", required_image=False, required_text=False)]
        payload = deepcopy(payload)
        payload["template"] = template.id
        payload["sections"] = []
        payload["justification"] = Justification(options=[JustificationOption(option="Da Apex", required_image=False, required_text=True)])

        form, _ = usecase(**payload)

        assert [option.option for option in form.justification.options] == ["Da Apex"]

    def test_create_form_usecase_with_template_not_found(self):
        usecase, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload["template"] = "d61dbf66-a10f-11ed-a8fc-0242ac1200ab"
        payload["sections"] = []

        try:
            usecase(**payload)
            assert False, "Expected NoItemsFound"
        except NoItemsFound as err:
            assert err.message == "Template não encontrado"

    def test_create_form_usecase_with_template_from_another_system(self):
        usecase, payload, template_repo = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload["template"] = template_repo.templates[0].id
        payload["sections"] = []
        payload["system"] = "JUNDIAI"

        with pytest.raises(ForbiddenAction):
            usecase(**payload)

    def test_create_form_usecase_with_inactive_template(self):
        usecase, payload, template_repo = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload["template"] = template_repo.templates[0].id
        payload["sections"] = []
        template_repo.templates[0].is_active = False

        with pytest.raises(ForbiddenAction):
            usecase(**payload)

    def test_create_form_usecase_duplicate_field_key(self):
        _, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)

        field_a = TextField(
            placeholder='placeholder',
            required=True,
            key='duplicate_key',
            regex='regex',
            formatting='formatting',
            max_length=10,
            value='value',
        )
        field_b = TextField(
            placeholder='placeholder',
            required=True,
            key='duplicate_key',
            regex='regex',
            formatting='formatting',
            max_length=10,
            value='value',
        )
        try:
            Section(section_id=1, fields=[field_a, field_b])
            assert False, "Expected EntityError"
        except EntityError as err:
            assert "Chaves de campo duplicadas na seção" in err.message


class TestCreateFormUsecaseUberlandiaPool:
    """Especificação Uberlândia §6/§9.1: `user_id` opcional (pool) via `SystemConfig`,
    e idempotência de criação por `external_id`."""

    def test_user_id_none_without_system_config_repo_raises(self):
        usecase, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload["user_id"] = None

        with pytest.raises(MissingParameters):
            usecase(**payload)

    def test_user_id_none_with_system_not_allowing_unassigned_raises(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        system_config_repo = SystemConfigRepositoryMock()
        system_config_repo.put(SystemConfig(system="GAIA", created_at=1, updated_at=1, allow_unassigned_forms=False))
        usecase = CreateFormUsecase(repo, file_repo, system_config_repo=system_config_repo)
        _, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload["user_id"] = None

        with pytest.raises(MissingParameters):
            usecase(**payload)

    def test_user_id_none_with_allow_unassigned_forms_creates_pool_form(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        system_config_repo = SystemConfigRepositoryMock()
        system_config_repo.put(SystemConfig(system="GAIA", created_at=1, updated_at=1, allow_unassigned_forms=True))
        usecase = CreateFormUsecase(repo, file_repo, system_config_repo=system_config_repo)
        _, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload["user_id"] = None

        form, files = usecase(**payload)

        assert form.user_id is None
        assert files == []

    def test_new_domain_fields_reach_the_created_form(self):
        usecase, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload.update(
            external_id="OS-7514",
            origin=FormOrigin.CITIZEN,
            service_type="tapa-buraco",
            occurred_at=1,
            scheduled_start_at=2,
            scheduled_end_at=3,
            attributes={"bairro": ["Santa Mônica"]},
        )

        form, _ = usecase(**payload)

        assert form.external_id == "OS-7514"
        assert form.origin == FormOrigin.CITIZEN
        assert form.service_type == "tapa-buraco"
        assert form.occurred_at == 1
        assert form.scheduled_start_at == 2
        assert form.scheduled_end_at == 3
        assert form.attributes == {"bairro": ["Santa Mônica"]}

    def test_external_id_replay_returns_existing_form_without_reprocessing_uploads(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = CreateFormUsecase(repo, file_repo)
        _, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload["external_id"] = "OS-7514"
        payload["information_fields"] = [FileInformationField(file_path="")]
        payload["information_fields_uploads"] = [FileUploadRequest(filename="a.jpg", mimetype="image/jpeg")]

        first_form, first_files = usecase(**payload)
        assert len(first_files) == 1

        second_form, second_files = usecase(**payload)

        assert second_form.id == first_form.id
        assert second_files == []
        assert len([f for f in repo.forms if f.external_id == "OS-7514"]) == 1


ADMIN_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
INSPECTOR_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"


class TestCreateFormUsecaseAppConfig:
    """O back recusa o que a configuração da aplicação esconde no app;
    quem administra o sistema (role ADMIN nele, ou super admin) não passa pela
    regra."""

    def _usecase(self, app_config=None, allow_unassigned_forms=False):
        system_config_repo = SystemConfigRepositoryMock()
        system_config_repo.put(SystemConfig(
            system="GAIA", created_at=1, updated_at=1,
            allow_unassigned_forms=allow_unassigned_forms, app_config=app_config,
        ))
        self.profile_repo = ProfileRepositoryMock()
        return CreateFormUsecase(
            FormRepositoryMock(), FileRepositoryMock(),
            system_config_repo=system_config_repo,
            access_control=AccessControl(self.profile_repo, SystemRoleRepositoryMock()),
        )

    def _payload(self, created_by, user_id):
        _, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload["created_by"] = created_by
        payload["user_id"] = user_id
        return payload

    def test_inspector_cannot_create_when_create_form_menu_is_off(self):
        usecase = self._usecase(app_config={"menus": {"create_form": False}})

        with pytest.raises(ForbiddenAction):
            usecase(**self._payload(INSPECTOR_ID, INSPECTOR_ID))

    def test_inspector_cannot_create_open_form_without_allow_open(self):
        usecase = self._usecase(allow_unassigned_forms=True)

        with pytest.raises(ForbiddenAction):
            usecase(**self._payload(INSPECTOR_ID, None))

    def test_inspector_cannot_create_open_form_when_system_does_not_accept_unassigned(self):
        usecase = self._usecase(app_config={"creation": {"allow_open": True}}, allow_unassigned_forms=False)

        with pytest.raises(ForbiddenAction):
            usecase(**self._payload(INSPECTOR_ID, None))

    def test_inspector_creates_open_form_when_both_flags_are_on(self):
        usecase = self._usecase(app_config={"creation": {"allow_open": True}}, allow_unassigned_forms=True)

        form, _ = usecase(**self._payload(INSPECTOR_ID, None))

        assert form.user_id is None

    def test_inspector_creates_own_form_with_default_config(self):
        usecase = self._usecase()

        form, _ = usecase(**self._payload(INSPECTOR_ID, INSPECTOR_ID))

        assert form.user_id == INSPECTOR_ID

    def test_admin_creates_open_form_even_with_create_form_menu_off(self):
        usecase = self._usecase(app_config={"menus": {"create_form": False}}, allow_unassigned_forms=True)

        form, _ = usecase(**self._payload(ADMIN_ID, None))

        assert form.user_id is None

    def test_system_admin_creates_even_with_create_form_menu_off(self):
        usecase = self._usecase(app_config={"menus": {"create_form": False}})
        self.profile_repo.put_membership(SystemMembership(
            user_id=INSPECTOR_ID, system="GAIA", role_id=ADMIN_ROLE_ID, created_at=1, updated_at=1,
        ))

        form, _ = usecase(**self._payload(INSPECTOR_ID, INSPECTOR_ID))

        assert form.user_id == INSPECTOR_ID

    def test_user_without_profile_follows_app_config(self):
        usecase = self._usecase(app_config={"menus": {"create_form": False}})

        with pytest.raises(ForbiddenAction):
            usecase(**self._payload("user-sem-perfil", "user-sem-perfil"))
