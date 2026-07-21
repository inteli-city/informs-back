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
from src.shared.domain.entities.file_upload import FileUploadRequest
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
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
