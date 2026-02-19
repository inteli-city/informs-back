import importlib
import json
import os
import sys
import uuid

sys.path.append(os.getcwd())

from src.shared.domain.entities.template import Template


class TestGetAllTemplatesPresenter:
    def test_get_all_templates_presenter(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.get_all_templates.app import get_all_templates_presenter

        importlib.reload(get_all_templates_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/templates",
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "name": "User",
                        "email": "user@test.com",
                        "cognito:groups": "FORMULARIOS,GAIA",
                    }
                }
            },
            "queryStringParameters": {"limit": 20, "is_active": True, "system": "GAIA"},
        }

        response = get_all_templates_presenter.lambda_handler(event, None)
        response_json = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert "templates" in response_json
        assert response_json["limit"] == 20
        assert response_json["system"] == "GAIA"
        assert response_json["systems"] == ["GAIA"]

    def test_get_all_templates_presenter_without_limit_returns_all_templates(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.get_all_templates.app import get_all_templates_presenter

        importlib.reload(get_all_templates_presenter)

        base = get_all_templates_presenter.repo.templates[0]
        inactive = Template(
            id=str(uuid.uuid4()),
            name=f"{base.name} Inactive",
            system=base.system,
            description=base.description,
            is_active=False,
            created_by=base.created_by,
            created_at=base.created_at,
            updated_at=base.updated_at,
            sections=base.sections,
        )
        get_all_templates_presenter.repo.templates.append(inactive)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/templates",
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "name": "User",
                        "email": "user@test.com",
                        "cognito:groups": "FORMULARIOS,GAIA",
                    }
                }
            },
            "queryStringParameters": {"system": "GAIA"},
        }

        response = get_all_templates_presenter.lambda_handler(event, None)
        response_json = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert "templates" in response_json
        assert response_json["limit"] is None
        assert response_json["last_evaluated_key"] is None
        assert len(response_json["templates"]) == 2
        assert any(template["is_active"] is False for template in response_json["templates"])
