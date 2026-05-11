import os
import sys

sys.path.append(os.getcwd())

from src.modules.plan_route.app.plan_route_controller import PlanRouteController
from src.modules.plan_route.app.plan_route_usecase import PlanRouteUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


REQUESTER_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"


def _requester_payload(sub: str = REQUESTER_USER_ID, groups: str = "FORMULARIOS") -> dict:
    return {
        "sub": sub,
        "name": "Tester",
        "email": "tester@example.com",
        "cognito:groups": groups,
    }


class TestPlanRouteController:
    def setup_method(self):
        self.repo = FormRepositoryMock()
        self.usecase = PlanRouteUsecase(self.repo)
        self.controller = PlanRouteController(self.usecase)

    def test_returns_200_with_ordered_forms_and_total_distance(self):
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "n": 5,
        })

        response = self.controller(request)

        assert response.status_code == 200
        assert "ordered_forms" in response.body
        assert "total_distance_km" in response.body
        assert isinstance(response.body["ordered_forms"], list)
        # mock tem 1 PENDING para esse user
        assert len(response.body["ordered_forms"]) == 1
        assert response.body["ordered_forms"][0]["order"] == 1

    def test_returns_200_empty_when_no_pending(self):
        # user 002 não tem PENDING no mock
        request = HttpRequest(body={
            "requester_user": _requester_payload(sub="d61dbf66-a10f-11ed-a8fc-0242ac120002"),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "n": 10,
        })

        response = self.controller(request)

        assert response.status_code == 200
        assert response.body["ordered_forms"] == []
        assert response.body["total_distance_km"] == 0.0

    def test_missing_requester_user_returns_400(self):
        request = HttpRequest(body={
            "start": {"latitude": -23.56, "longitude": -46.65},
            "n": 5,
        })

        response = self.controller(request)

        assert response.status_code == 400

    def test_missing_start_returns_400(self):
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "n": 5,
        })

        response = self.controller(request)

        assert response.status_code == 400

    def test_missing_both_n_and_form_ids_returns_400(self):
        # Sem n nem form_ids — XOR não permite vazio.
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
        })

        response = self.controller(request)

        assert response.status_code == 400

    def test_both_n_and_form_ids_returns_400(self):
        # XOR — passar ambos é inválido.
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "n": 5,
            "form_ids": ["d61dbf66-a10f-11ed-a8fc-0242ac120012"],
        })

        response = self.controller(request)

        assert response.status_code == 400

    def test_n_zero_returns_400(self):
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "n": 0,
        })

        response = self.controller(request)

        assert response.status_code == 400

    def test_n_above_limit_returns_400(self):
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "n": 51,  # limite é 50
        })

        response = self.controller(request)

        assert response.status_code == 400

    def test_invalid_latitude_returns_400(self):
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": 91.0, "longitude": -46.65},  # > 90
            "n": 5,
        })

        response = self.controller(request)

        assert response.status_code == 400

    def test_invalid_longitude_returns_400(self):
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -181.0},  # < -180
            "n": 5,
        })

        response = self.controller(request)

        assert response.status_code == 400

    def test_with_optional_end_returns_200(self):
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "end": {"latitude": -23.58, "longitude": -46.63},
            "n": 5,
        })

        response = self.controller(request)

        assert response.status_code == 200

    def test_user_without_formularios_group_returns_403(self):
        request = HttpRequest(body={
            "requester_user": _requester_payload(groups="SGC,INTELIFLEETS"),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "n": 5,
        })

        response = self.controller(request)

        assert response.status_code == 403

    def test_form_ids_mode_returns_200(self):
        # form 2 do mock é PENDING e pertence ao REQUESTER_USER_ID
        valid_form_id = self.repo.forms[2].id
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "form_ids": [valid_form_id],
        })

        response = self.controller(request)

        assert response.status_code == 200
        assert len(response.body["ordered_forms"]) == 1
        assert response.body["ordered_forms"][0]["form_id"] == valid_form_id

    def test_form_ids_mode_with_missing_id_returns_404_with_missing_list(self):
        valid_form_id = self.repo.forms[2].id
        invalid_form_id = "00000000-0000-0000-0000-000000000000"
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "form_ids": [valid_form_id, invalid_form_id],
        })

        response = self.controller(request)

        assert response.status_code == 404
        assert isinstance(response.body, dict)
        assert response.body["missing_form_ids"] == [invalid_form_id]

    def test_form_ids_mode_with_id_of_other_user_returns_404(self):
        # form 1 do mock pertence ao user 002 (não ao requester)
        other_user_form_id = self.repo.forms[1].id
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "form_ids": [other_user_form_id],
        })

        response = self.controller(request)

        assert response.status_code == 404
        assert response.body["missing_form_ids"] == [other_user_form_id]

    def test_empty_form_ids_returns_400(self):
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "form_ids": [],
        })

        response = self.controller(request)

        assert response.status_code == 400

    def test_form_ids_above_limit_returns_400(self):
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "form_ids": [f"id-{i}" for i in range(51)],  # limite é 50
        })

        response = self.controller(request)

        assert response.status_code == 400

    def test_unexpected_error_returns_500(self):
        class BoomUsecase:
            def __call__(self, **kwargs):
                raise Exception("boom")

        controller = PlanRouteController(BoomUsecase())
        request = HttpRequest(body={
            "requester_user": _requester_payload(),
            "start": {"latitude": -23.56, "longitude": -46.65},
            "n": 5,
        })

        response = controller(request)

        assert response.status_code == 500
        assert response.body == "boom"
