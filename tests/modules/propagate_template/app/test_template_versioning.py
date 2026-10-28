import json
import os
import sys
import uuid
from copy import deepcopy

import pytest

sys.path.append(os.getcwd())

from src.modules.get_template_forms.app.get_template_forms_controller import GetTemplateFormsController
from src.modules.get_template_forms.app.get_template_forms_usecase import GetTemplateFormsUsecase
from src.modules.propagate_template.app.propagate_template_controller import PropagateTemplateController
from src.modules.propagate_template.app.propagate_template_usecase import PropagateTemplateUsecase
from src.modules.submit_form.app.submit_form_usecase import SubmitFormUsecase
from src.modules.update_template.app.update_template_controller import UpdateTemplateController
from src.modules.update_template.app.update_template_usecase import UpdateTemplateUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import TemplateVersionRequired
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.dtos.user_gateway import UserGatewayDTO
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock

USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
REQUESTER = UserGatewayDTO(user_id=USER_ID, email="admin@x.com", name="Admin", systems=["GAIA"])
CLAIMS = {"sub": USER_ID, "email": "admin@x.com", "name": "Admin", "cognito:groups": "FORMULARIOS,GAIA"}


def _form(template_id: str, status: FormStatus, template_version: int = 1, created_at: int = 1) -> Form:
    return Form(
        id=str(uuid.uuid4()),
        form_title=f"OS {status.value}",
        created_by=USER_ID,
        user_id=USER_ID,
        template=template_id,
        template_version=template_version,
        system="GAIA",
        city="Uberlândia",
        street="Rua 1",
        latitude=-18.9,
        longitude=-48.2,
        priority=Priority.MEDIUM,
        status=status,
        created_at=created_at,
        updated_at=created_at,
        sections=[Section(section_id=1, fields=[TextField(label="Nome", required=True, key="name", order=1)])],
        justification=Justification(options=[JustificationOption(option="Sem acesso", required_image=False, required_text=False)]),
    )


NEW_SECTIONS = [
    Section(
        section_id=1,
        fields=[
            TextField(label="Nome", required=True, key="name", order=1),
            TextField(label="Placa do poste", required=True, key="plate", order=2),
        ],
    )
]


class TestTemplateVersioning:
    def setup_method(self):
        self.template_repo = TemplateRepositoryMock()
        self.form_repo = FormRepositoryMock()
        self.template = self.template_repo.templates[0]
        self.update = UpdateTemplateUsecase(self.template_repo, form_repo=self.form_repo)

    def _add(self, *forms: Form):
        self.form_repo.forms.extend(forms)

    # ---- edição -----------------------------------------------------------

    def test_free_edit_when_no_form_uses_the_template(self):
        updated = self.update(template_id=self.template.id, requester_user_id=USER_ID, sections=deepcopy(NEW_SECTIONS))

        assert len(updated.sections[0].fields) == 2
        assert updated.version == 1

    def test_in_use_template_refuses_field_change_without_new_version(self):
        self._add(_form(self.template.id, FormStatus.CANCELLED))

        with pytest.raises(TemplateVersionRequired):
            self.update(template_id=self.template.id, requester_user_id=USER_ID, sections=deepcopy(NEW_SECTIONS))

    def test_in_use_template_refuses_reason_change_without_new_version(self):
        self._add(_form(self.template.id, FormStatus.PENDING))

        with pytest.raises(TemplateVersionRequired):
            self.update(
                template_id=self.template.id,
                requester_user_id=USER_ID,
                justification_options=[JustificationOption(option="Chuva", required_image=False, required_text=False)],
            )

    def test_in_use_template_accepts_same_content_and_metadata(self):
        """O app manda o template inteiro a cada salvar: reenviar as mesmas
        seções não é mudança, e o nome muda sem nova versão."""
        self._add(_form(self.template.id, FormStatus.PENDING))

        updated = self.update(
            template_id=self.template.id,
            requester_user_id=USER_ID,
            name="Nome novo",
            sections=deepcopy(self.template.sections),
        )

        assert updated.name == "Nome novo"
        assert updated.version == 1

    def test_new_version_bumps_version(self):
        self._add(_form(self.template.id, FormStatus.PENDING))

        updated = self.update(
            template_id=self.template.id, requester_user_id=USER_ID, sections=deepcopy(NEW_SECTIONS), new_version=True,
        )

        assert updated.version == 2
        assert [field.key for field in updated.sections[0].fields] == ["name", "plate"]

    def test_controller_answers_409_when_new_version_is_required(self):
        self._add(_form(self.template.id, FormStatus.PENDING))
        controller = UpdateTemplateController(self.update)
        request = HttpRequest(body={
            "requester_user": CLAIMS,
            "template_id": self.template.id,
            "sections": [{"section_id": 9, "fields": [
                {"field_type": "TEXT_FIELD", "label": "Outro", "required": True, "key": "other", "order": 1},
            ]}],
        })

        response = controller(request)

        assert response.status_code == 409
        assert "nova versão" in str(response.body)

    # ---- listagem por template ---------------------------------------------

    def test_lists_only_open_forms_by_default(self):
        pending = _form(self.template.id, FormStatus.PENDING, created_at=1)
        running = _form(self.template.id, FormStatus.IN_PROGRESS, created_at=2)
        done = _form(self.template.id, FormStatus.COMPLETED, created_at=3)
        cancelled = _form(self.template.id, FormStatus.CANCELLED, created_at=4)
        self._add(pending, running, done, cancelled)
        usecase = GetTemplateFormsUsecase(self.template_repo, self.form_repo)

        open_page = usecase(template_id=self.template.id, requester=REQUESTER)
        all_page = usecase(template_id=self.template.id, requester=REQUESTER, only_open=False)

        assert [form.id for form in open_page.forms] == [pending.id, running.id]
        assert open_page.in_use is True
        assert len(all_page.forms) == 4

    def test_in_use_even_when_no_form_is_open(self):
        self._add(_form(self.template.id, FormStatus.COMPLETED))
        page = GetTemplateFormsUsecase(self.template_repo, self.form_repo)(template_id=self.template.id, requester=REQUESTER)

        assert page.forms == []
        assert page.in_use is True

    def test_lists_in_pages(self):
        self._add(*[_form(self.template.id, FormStatus.PENDING, created_at=i) for i in range(5)])
        controller = GetTemplateFormsController(GetTemplateFormsUsecase(self.template_repo, self.form_repo))

        first = controller(HttpRequest(body={"requester_user": CLAIMS, "template_id": self.template.id, "limit": "2"}))
        body = first.body if isinstance(first.body, dict) else json.loads(first.body)
        second = controller(HttpRequest(body={
            "requester_user": CLAIMS, "template_id": self.template.id, "limit": "2",
            "exclusive_start_key": body["last_evaluated_key"],
        }))
        body2 = second.body if isinstance(second.body, dict) else json.loads(second.body)

        assert first.status_code == 200
        assert len(body["forms"]) == 2 and body["last_evaluated_key"]
        assert {form["id"] for form in body["forms"]}.isdisjoint({form["id"] for form in body2["forms"]})
        assert body["template_version"] == 1

    # ---- propagação ---------------------------------------------------------

    def _bump(self):
        self._add(_form(self.template.id, FormStatus.CANCELLED))
        return self.update(
            template_id=self.template.id, requester_user_id=USER_ID, sections=deepcopy(NEW_SECTIONS), new_version=True,
        )

    def test_propagates_open_forms_and_skips_the_rest(self):
        pending = _form(self.template.id, FormStatus.PENDING)
        running = _form(self.template.id, FormStatus.IN_PROGRESS)
        done = _form(self.template.id, FormStatus.COMPLETED)
        other = _form(str(uuid.uuid4()), FormStatus.PENDING)
        self._add(pending, running, done, other)
        self._bump()

        result = PropagateTemplateUsecase(self.template_repo, self.form_repo)(
            template_id=self.template.id,
            requester=REQUESTER,
            form_ids=[pending.id, running.id, done.id, other.id, "nao-existe", pending.id],
        )

        assert result.template_version == 2
        assert result.updated == [pending.id, running.id]
        assert dict(result.skipped) == {
            done.id: "closed", other.id: "other_template", "nao-existe": "not_found",
        }
        stored = self.form_repo.get_form_by_id(USER_ID, pending.id)
        assert stored.template_version == 2
        assert [field.key for field in stored.sections[0].fields] == ["name", "plate"]

    def test_already_current_is_skipped(self):
        self._bump()
        current = _form(self.template.id, FormStatus.PENDING, template_version=2)
        self._add(current)

        result = PropagateTemplateUsecase(self.template_repo, self.form_repo)(
            template_id=self.template.id, requester=REQUESTER, form_ids=[current.id],
        )

        assert result.updated == []
        assert result.skipped == [(current.id, "already_current")]

    def test_propagate_limits_batch_size(self):
        controller = PropagateTemplateController(PropagateTemplateUsecase(self.template_repo, self.form_repo))
        response = controller(HttpRequest(body={
            "requester_user": CLAIMS, "template_id": self.template.id,
            "form_ids": [str(uuid.uuid4()) for _ in range(101)],
        }))

        assert response.status_code == 400

    # ---- envio contra versão anterior ---------------------------------------

    def _running_on_v2(self) -> Form:
        form = _form(self.template.id, FormStatus.IN_PROGRESS, template_version=2)
        form.sections = deepcopy(NEW_SECTIONS)
        self.form_repo.forms = [form]
        return form

    def test_submit_filled_on_older_version_is_accepted(self):
        form = self._running_on_v2()
        submit = SubmitFormUsecase(self.form_repo, FileRepositoryMock())

        submit(
            user_id=USER_ID,
            form_id=form.id,
            # "obs" não existe mais; "plate", obrigatório na v2, não veio.
            fields=[
                {"section_id": 1, "section_instance": 0, "field_key": "name", "value": "Ana"},
                {"section_id": 1, "section_instance": 0, "field_key": "obs", "value": "antigo"},
            ],
            completed_at=10,
            template_version=1,
        )

        stored = self.form_repo.get_form_by_id(USER_ID, form.id)
        assert stored.status is FormStatus.COMPLETED
        assert stored.sections[0].fields[0].value == "Ana"

    def test_submit_on_current_version_stays_strict(self):
        form = self._running_on_v2()
        submit = SubmitFormUsecase(self.form_repo, FileRepositoryMock())

        with pytest.raises(EntityError):
            submit(
                user_id=USER_ID,
                form_id=form.id,
                fields=[{"section_id": 1, "section_instance": 0, "field_key": "obs", "value": "x"}],
                completed_at=10,
                template_version=2,
            )


class TestTemplateIndexDynamoMapping:
    """Sem AWS: só o formato das chaves do `TemplateIndex` e a leitura do item
    projetado."""

    def test_only_forms_from_a_template_enter_the_index(self):
        from src.shared.infra.repositories.form_repository_dynamo import FormRepositoryDynamo

        template_id = str(uuid.uuid4())
        form = _form(template_id, FormStatus.PENDING, created_at=946407600000)
        keys = FormRepositoryDynamo.template_index_keys(form)

        assert keys == {
            "GSI4PK": f"template#{template_id}",
            "GSI4SK": f"created_at#0946407600000#{form.id}",
        }
        inline = _form(template_id, FormStatus.PENDING)
        inline.template = None
        assert FormRepositoryDynamo.template_index_keys(inline) == {}

    def test_reads_projected_item_with_pre_versioning_defaults(self):
        from src.shared.infra.repositories.form_repository_dynamo import FormRepositoryDynamo

        summary = FormRepositoryDynamo._template_form_summary({
            "PK": "form#abc",
            "form_title": "OS",
            "system": "GAIA",
            "status": "PENDING",
            "created_at": 5,
            "street": "Rua 1",
        })

        assert summary.id == "abc"
        assert summary.template_version == 1
        assert summary.possession.value == "OPEN"
        assert summary.is_open()
