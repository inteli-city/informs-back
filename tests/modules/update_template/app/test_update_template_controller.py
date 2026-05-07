import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.append(os.getcwd())

from src.modules.update_template.app.update_template_controller import UpdateTemplateController
from src.modules.update_template.app.update_template_usecase import UpdateTemplateUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.field import TextField


class TestUpdateTemplateController:
    def setup_method(self):
        self.repo = TemplateRepositoryMock()
        self.usecase = UpdateTemplateUsecase(self.repo)
        self.controller = UpdateTemplateController(self.usecase)
        self.template = self.repo.templates[0]

    def test_update_template_controller_success(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": "user-1",
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS,GAIA",
            },
            "template_id": self.template.id,
            "name": "Controller Update",
            "description": "Desc",
            "is_active": False,
        })

        response = self.controller(request)

        assert response.status_code == 200
        assert response.body["name"] == "Controller Update"
        assert response.body["is_active"] is False

    def test_update_template_controller_with_sections(self):
        section = {
            "section_id": 2,
            "fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "label": "Label",
                    "required": True,
                    "key": "key",
                    "order": 1,
                    "regex": None,
                    "max_length": None,
                    "help_text": None,
                    "formatting": None,
                }
            ]
        }
        request = HttpRequest(body={
            "requester_user": {"sub": "user-1", "name": "Tester", "email": "t@example.com", "cognito:groups": "FORMULARIOS,GAIA"},
            "template_id": self.template.id,
            "sections": [section],
        })

        response = self.controller(request)
        assert response.status_code == 200
        assert response.body["sections"][0]["section_id"] == 2

    def test_update_template_controller_missing_template_id(self):
        request = HttpRequest(body={
            "requester_user": {"sub": "user-1", "name": "Tester", "email": "t@example.com", "cognito:groups": "FORMULARIOS,GAIA"},
        })

        response = self.controller(request)
        assert response.status_code == 400

    def test_update_template_controller_wrong_type(self):
        request = HttpRequest(body={
            "requester_user": {"sub": "user-1", "name": "Tester", "email": "t@example.com", "cognito:groups": "FORMULARIOS,GAIA"},
            "template_id": self.template.id,
            "is_active": "yes",
        })

        response = self.controller(request)
        assert response.status_code == 400

    def test_update_template_controller_accepts_legacy_isActive(self):
        request = HttpRequest(body={
            "requester_user": {"sub": "user-1", "name": "Tester", "email": "t@example.com", "cognito:groups": "FORMULARIOS,GAIA"},
            "template_id": self.template.id,
            "isActive": False,
        })

        response = self.controller(request)
        assert response.status_code == 200
        assert response.body["is_active"] is False

    def test_update_template_controller_forbidden_existing_system(self):
        request = HttpRequest(body={
            "requester_user": {"sub": "user-1", "name": "Tester", "email": "t@example.com", "cognito:groups": "FORMULARIOS,ORION"},
            "template_id": self.template.id,
            "name": "Blocked",
        })

        response = self.controller(request)
        assert response.status_code == 403
        assert "permissão" in response.body

    def test_update_template_controller_forbidden_target_system(self):
        request = HttpRequest(body={
            "requester_user": {"sub": "user-1", "name": "Tester", "email": "t@example.com", "cognito:groups": "FORMULARIOS,GAIA"},
            "template_id": self.template.id,
            "system": "ORION",
        })

        response = self.controller(request)
        assert response.status_code == 403
        assert "permissão" in response.body
