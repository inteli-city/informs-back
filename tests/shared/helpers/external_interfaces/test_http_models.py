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

    def test_non_overlapping_keys_still_merge_normally(self):
        request = HttpRequest(
            body={"form_title": "x"},
            headers={"authorization": "Bearer y"},
            query_params={"limit": "10"},
            path_params={"formId": "abc"},
        )
        assert request.data == {
            "form_title": "x",
            "authorization": "Bearer y",
            "limit": "10",
            "formId": "abc",
        }

    def test_overlap_still_emits_warning(self):
        """A sobreposição continua sendo sinalizada — só a precedência mudou."""
        with pytest.warns(UserWarning, match="priority"):
            HttpRequest(body={"priority": 1}, headers={"priority": "u=4"})
