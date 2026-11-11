import pytest

from src.shared.helpers.external_interfaces.http_models import HttpRequest


class TestHttpRequestDataPrecedence:

    def test_body_wins_over_header_with_same_key(self):
        """Reproduz o bug real: o header HTTP padrão `Priority` (RFC 9218),
        enviado automaticamente por fetch()/XHR de navegadores modernos,
        chega em lowercase (`priority`) e colidia com o campo de negócio
        `priority` do body, sobrescrevendo o int correto por uma string."""
        request = HttpRequest(
            body={"priority": 1, "form_title": "x"},
            headers={"priority": "u=4", "content-type": "application/json"},
        )
        assert request.data["priority"] == 1
        assert isinstance(request.data["priority"], int)

    def test_body_wins_over_query_param_with_same_key(self):
        request = HttpRequest(
            body={"status": "ACTIVE"},
            query_params={"status": "queried"},
        )
        assert request.data["status"] == "ACTIVE"

    def test_body_wins_over_path_param_with_same_key(self):
        request = HttpRequest(
            body={"user_id": "from-body"},
            path_params={"user_id": "from-path"},
        )
        assert request.data["user_id"] == "from-body"

    def test_body_query_and_path_merge_but_headers_do_not(self):
        request = HttpRequest(
            body={"form_title": "x"},
            headers={"authorization": "Bearer y"},
            query_params={"limit": "10"},
            path_params={"formId": "abc"},
        )
        assert request.data == {"form_title": "x", "limit": "10", "formId": "abc"}
        assert request.headers == {"authorization": "Bearer y"}

    def test_browser_origin_header_does_not_become_a_parameter(self):
        """Bug real: todo POST do app web leva o header `Origin`, que virava o
        campo opcional `origin` do POST /forms (CITIZEN, ...) e dava 400."""
        request = HttpRequest(
            body={"form_title": "x"},
            headers={"origin": "https://dev.example.amplifyapp.com"},
        )
        assert "origin" not in request.data

    def test_overlap_with_query_still_emits_warning(self):
        with pytest.warns(UserWarning, match="status"):
            HttpRequest(body={"status": "ACTIVE"}, query_params={"status": "queried"})
