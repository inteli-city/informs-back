import json
import os
import sys

os.environ["STAGE"] = "TEST"
sys.path.append(os.getcwd())

from src.modules.update_template.app.update_template_presenter import lambda_handler, repo


class TestUpdateTemplatePresenter:
    def test_update_template_presenter(self):
        template = repo.templates[0]
        event = {
            "version": "2.0",
            "routeKey": "PUT /templates/{template_id}",
            "rawPath": "/templates/{template_id}",
            "rawQueryString": "",
            "requestContext": {
                "authorizer": {"claims": {"sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001", "name": "Tester", "email": "t@example.com", "cognito:groups": "FORMULARIOS,GAIA"}},
            },
            "pathParameters": {"template_id": template.id},
            "body": json.dumps({
                "name": "Presenter Updated",
                "is_active": False
            })
        }

        response = lambda_handler(event, None)
        response_json = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert response_json["name"] == "Presenter Updated"
        assert response_json["is_active"] is False

    def test_update_template_presenter_devolve_os_campos_informativos(self):
        # Regressão: a resposta do PUT devolvia os objetos TemplateInformationField crus e a validação do
        # retorno falhava com 400 depois de o requisito já ter sido gravado (create e get convertem com to_dict()).
        template = repo.templates[0]
        event = {
            "version": "2.0",
            "routeKey": "PUT /templates/{template_id}",
            "rawPath": "/templates/{template_id}",
            "rawQueryString": "",
            "requestContext": {
                "authorizer": {"claims": {"sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001", "name": "Tester", "email": "t@example.com", "cognito:groups": "FORMULARIOS,GAIA"}},
            },
            "pathParameters": {"template_id": template.id},
            "body": json.dumps({
                "name": "Presenter Updated",
                "is_active": True,
                "information_fields": [
                    {"key": "foto-do-local", "label": "Foto do local", "information_field_type": "FILE_INFORMATION_FIELD",
                     "required": True, "file_type": "IMAGE"}
                ],
            })
        }

        response = lambda_handler(event, None)
        response_json = json.loads(response["body"])

        assert response["statusCode"] == 200, response["body"]
        assert response_json["information_fields"][0]["key"] == "foto-do-local"
        assert response_json["information_fields"][0]["required"] is True
