from src.modules.get_permission_actions.app.get_permission_actions_controller import GetPermissionActionsController
from src.modules.get_permission_actions.app.get_permission_actions_usecase import GetPermissionActionsUsecase
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import INSPECTOR_ID, requester_user


class TestGetPermissionActions:
    def test_lists_the_whole_catalog_with_descriptions(self):
        controller = GetPermissionActionsController(GetPermissionActionsUsecase())

        response = controller(HttpRequest(body={"requester_user": requester_user(INSPECTOR_ID)}))

        assert response.status_code == 200
        assert [item["action"] for item in response.body["actions"]] == [action.value for action in Action]
        assert all(item["description"] for item in response.body["actions"])

    def test_missing_requester_returns_400(self):
        controller = GetPermissionActionsController(GetPermissionActionsUsecase())
        assert controller(HttpRequest(body={})).status_code == 400
