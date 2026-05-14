"""Testes do GetLocationHistoryController.

Cobre status codes esperados (200 OK, 400 invalid range, 403 forbidden,
400 missing params) e a propagação correta dos query params até o usecase.
"""

import os
import sys
from typing import Optional

sys.path.append(os.getcwd())

from src.modules.get_location_history.app.get_location_history_controller import (
    GetLocationHistoryController,
)
from src.modules.get_location_history.app.get_location_history_usecase import (
    GetLocationHistoryUsecase,
)
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.location_repository_mock import (
    LocationRepositoryMock,
)
from src.shared.infra.repositories.profile_repository_mock import (
    ProfileRepositoryMock,
)


ADMIN_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
INSPECTOR_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"
TARGET = "fake-inspector-id"


def _requester_user(sub: str = ADMIN_ID, groups: str = "FORMULARIOS,GAIA"):
    return {
        "sub": sub,
        "name": "Tester",
        "email": "tester@example.com",
        "cognito:groups": groups,
    }


def _request(
    *,
    requester_sub: str = ADMIN_ID,
    user_id: Optional[str] = TARGET,
    since: Optional[int] = 1,
    until: Optional[int] = 10_000,
):
    body = {"requester_user": _requester_user(sub=requester_sub)}
    if user_id is not None:
        body["user_id"] = user_id
    if since is not None:
        body["since"] = since
    if until is not None:
        body["until"] = until
    return HttpRequest(body=body)


class TestGetLocationHistoryController:
    def setup_method(self):
        self.location_repo = LocationRepositoryMock()
        self.profile_repo = ProfileRepositoryMock()
        self.usecase = GetLocationHistoryUsecase(
            location_repo=self.location_repo, profile_repo=self.profile_repo
        )
        self.controller = GetLocationHistoryController(self.usecase)

    def test_admin_full_range_returns_200(self):
        resp = self.controller(_request())
        assert resp.status_code == 200
        assert resp.body["count"] == 5
        assert len(resp.body["items"]) == 5

    def test_admin_filtered_range_returns_200(self):
        resp = self.controller(_request(since=2000, until=4000))
        assert resp.status_code == 200
        assert resp.body["count"] == 3
        assert [i["ts"] for i in resp.body["items"]] == [2000, 3000, 4000]

    def test_inspector_returns_403(self):
        resp = self.controller(_request(requester_sub=INSPECTOR_ID))
        assert resp.status_code == 403

    def test_inverted_range_returns_400(self):
        resp = self.controller(_request(since=5000, until=1000))
        assert resp.status_code == 400

    def test_missing_user_id_returns_400(self):
        resp = self.controller(_request(user_id=None))
        assert resp.status_code == 400

    def test_zero_since_returns_400(self):
        # Schema exige since > 0 (gt=0), então since=0 quebra.
        resp = self.controller(_request(since=0, until=1000))
        assert resp.status_code == 400

    def test_unknown_target_returns_200_with_empty(self):
        resp = self.controller(_request(user_id="ghost"))
        assert resp.status_code == 200
        assert resp.body["items"] == []
        assert resp.body["count"] == 0

    def test_default_since_until_uses_today_brt_to_now(self, monkeypatch):
        """Sem since/until, controller assume 00:00 BRT até agora.
        Mocamos as funções de default pra passar valores controlados."""
        from src.modules.get_location_history.app import (
            get_location_history_controller as ctrl_module,
        )
        # Default cobre 100% do range do mock (1000..5000).
        monkeypatch.setattr(ctrl_module, "_default_since_ms", lambda: 1)
        monkeypatch.setattr(ctrl_module, "_default_until_ms", lambda: 9999)

        resp = self.controller(_request(since=None, until=None))
        assert resp.status_code == 200
        assert resp.body["count"] == 5

    def test_default_only_until(self, monkeypatch):
        """Cliente passa só since; until vira agora."""
        from src.modules.get_location_history.app import (
            get_location_history_controller as ctrl_module,
        )
        monkeypatch.setattr(ctrl_module, "_default_until_ms", lambda: 9999)

        resp = self.controller(_request(since=2000, until=None))
        # Pega 2000..5000 (4 pings).
        assert resp.status_code == 200
        assert resp.body["count"] == 4
