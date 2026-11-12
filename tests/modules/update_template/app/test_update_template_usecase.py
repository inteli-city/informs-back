import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.append(os.getcwd())

from src.modules.update_template.app.update_template_usecase import UpdateTemplateUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import NoItemsFound
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


class TestUpdateTemplateUsecase:
    def setup_method(self):
        self.repo = TemplateRepositoryMock()
        self.usecase = UpdateTemplateUsecase(self.repo)
        self.existing = self.repo.templates[0]

    def test_update_template_success_partial(self):
        updated = self.usecase(
            template_id=self.existing.id,
            requester_user_id="user-1",
            name="Updated Name",
            description="New desc",
        )

        assert updated.name == "Updated Name"
        assert updated.description == "New desc"
        assert updated.system == self.existing.system
        assert updated.sections == self.existing.sections
        assert isinstance(updated.updated_at, int)

    def test_update_template_with_sections(self):
        new_section = Section(section_id=2, fields=[TextField(label="Other", required=True, key="other", order=1)])
        updated = self.usecase(
            template_id=self.existing.id,
            requester_user_id="user-1",
            sections=[new_section],
            is_active=False,
        )
        assert updated.sections[0].section_id == 2
        assert updated.is_active is False

    def test_update_template_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(
                template_id="non-existent",
                requester_user_id="user-1",
                name="Any",
            )

    def test_update_template_invalid_sections(self):
        with pytest.raises(EntityError):
            self.usecase(
                template_id=self.existing.id,
                requester_user_id="user-1",
                sections=[],
            )


from src.shared.domain.entities.template_information_field import TemplateInformationField
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.information_field_type_enum import InformationFieldType


def test_information_field_change_saves_in_place_even_when_template_is_used():
    """Campos informativos valem só para formulários criados depois: mudar só
    eles não cria versão nem pede `new_version`."""
    from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
    repo = TemplateRepositoryMock()
    template = repo.templates[0]
    forms = FormRepositoryMock()
    forms.has_forms_with_template = lambda _: True
    usecase = UpdateTemplateUsecase(repo, form_repo=forms)
    fields = [TemplateInformationField(
        key="evidencia", label="Evidência", information_field_type=InformationFieldType.FILE_INFORMATION_FIELD,
        required=True, file_type=FileType.IMAGE,
    )]
    updated = usecase(template_id=template.id, requester_user_id="user", information_fields=fields)
    assert updated.version == 1
    assert updated.information_fields == fields
    from src.shared.infra.dtos.template_dynamo_dto import TemplateDynamoDTO
    dto = TemplateDynamoDTO.from_entity(updated)
    record = {**dto.to_dynamo(), "PK": f"template#{template.id}"}
    assert TemplateDynamoDTO.from_dynamo(record).to_entity().information_fields == fields
    # O editor antigo ainda manda new_version=True: sem mudança de conteúdo, não sobe a versão.
    again = usecase(template_id=template.id, requester_user_id="user", information_fields=[], new_version=True)
    assert again.version == 1
    assert again.information_fields == []
