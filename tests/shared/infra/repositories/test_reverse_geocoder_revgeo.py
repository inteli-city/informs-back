import io
import json
import os
import sys
import urllib.error
import urllib.parse

import pytest

sys.path.append(os.getcwd())

from src.shared.domain.entities.geocoded_address import GeocodedAddress
from src.shared.helpers.errors.usecase_errors import ReverseGeocodeUnavailable
from src.shared.infra.repositories.reverse_geocoder_revgeo import ReverseGeocoderRevgeo, parse_nominatim
from tests.shared.infra.repositories.fakes_apex import FakeResponse

MODULE = "src.shared.infra.repositories.reverse_geocoder_revgeo.urllib.request.urlopen"

NOMINATIM_RESULT = {
    "display_name": "2121, Avenida João Naves de Ávila, Santa Mônica, Uberlândia, Minas Gerais, 38408-100, Brasil",
    "address": {
        "house_number": "2121",
        "road": "Avenida João Naves de Ávila",
        "suburb": "Santa Mônica",
        "city": "Uberlândia",
        "state": "Minas Gerais",
        "postcode": "38408-100",
        "country": "Brasil",
    },
}


def _geocoder():
    geocoder = ReverseGeocoderRevgeo()
    geocoder.base_url = "https://revgeo.example/revgeo"
    geocoder.api_key = "chave-de-teste"
    geocoder.timeout = 5
    return geocoder


class TestParseNominatim:
    def test_reads_street_number_city_and_display_name(self):
        assert parse_nominatim(NOMINATIM_RESULT) == GeocodedAddress(
            street="Avenida João Naves de Ávila",
            number="2121",
            city="Uberlândia",
            formatted=NOMINATIM_RESULT["display_name"],
        )

    def test_small_town_comes_as_town(self):
        result = {"display_name": "x", "address": {"road": "Rua A", "town": "Araguari"}}
        assert parse_nominatim(result).city == "Araguari"

    def test_point_without_address_is_none(self):
        assert parse_nominatim({"error": "Unable to geocode"}) is None
        assert parse_nominatim({"display_name": "Oceano", "address": {"country": "Brasil"}}) is None
        assert parse_nominatim(None) is None

    def test_accepts_list_result(self):
        assert parse_nominatim([NOMINATIM_RESULT]).street == "Avenida João Naves de Ávila"


class TestReverseGeocoderRevgeo:
    def test_calls_nominatim_route_with_key_and_parses(self, monkeypatch):
        calls = []

        def fake_urlopen(req, timeout):
            calls.append((req, timeout))
            return FakeResponse(200, json.dumps({"provider": "nominatim", "result": NOMINATIM_RESULT}))

        monkeypatch.setattr(MODULE, fake_urlopen)

        address = _geocoder().reverse(-18.918, -48.2772)

        assert address.city == "Uberlândia"
        request, timeout = calls[0]
        url = urllib.parse.urlsplit(request.full_url)
        assert url.path == "/revgeo/api/geocode/nominatim"
        query = dict(urllib.parse.parse_qsl(url.query))
        assert query["lat"] == "-18.918" and query["lng"] == "-48.2772"
        assert query["addressdetails"] == "true"
        assert request.get_header("X-api-key") == "chave-de-teste"
        assert timeout == 5

    def test_sends_its_own_user_agent(self, monkeypatch):
        # O Cloudflare do backend.inteli.city recusa o User-Agent padrão do urllib (HTTP 403, código 1010) e deixaria
        # o endereço do pin sempre indisponível no deploy. Achado no E2E local com a chave real.
        calls = []

        def fake_urlopen(req, timeout):
            calls.append(req)
            return FakeResponse(200, json.dumps({"provider": "nominatim", "result": NOMINATIM_RESULT}))

        monkeypatch.setattr(MODULE, fake_urlopen)

        _geocoder().reverse(-18.918, -48.2772)

        user_agent = calls[0].get_header("User-agent")
        assert user_agent and not user_agent.startswith("Python-urllib")

    def test_without_address_returns_none(self, monkeypatch):
        monkeypatch.setattr(MODULE, lambda req, timeout: FakeResponse(
            200, json.dumps({"provider": "nominatim", "result": {"error": "Unable to geocode"}})
        ))
        assert _geocoder().reverse(0.0, 0.0) is None

    @pytest.mark.parametrize("failure", [
        urllib.error.HTTPError("u", 401, "Unauthorized", {}, io.BytesIO(b"")),
        urllib.error.URLError("sem rede"),
        TimeoutError(),
    ])
    def test_service_failures_become_unavailable(self, monkeypatch, failure):
        def fake_urlopen(req, timeout):
            raise failure

        monkeypatch.setattr(MODULE, fake_urlopen)
        with pytest.raises(ReverseGeocodeUnavailable):
            _geocoder().reverse(-18.918, -48.2772)

    def test_unexpected_body_is_unavailable(self, monkeypatch):
        monkeypatch.setattr(MODULE, lambda req, timeout: FakeResponse(200, '{"detail": "?"}'))
        with pytest.raises(ReverseGeocodeUnavailable):
            _geocoder().reverse(-18.918, -48.2772)

    def test_without_key_does_not_call_the_service(self, monkeypatch):
        monkeypatch.setattr(MODULE, lambda req, timeout: pytest.fail("não deveria chamar o serviço"))
        geocoder = _geocoder()
        geocoder.api_key = None
        with pytest.raises(ReverseGeocodeUnavailable):
            geocoder.reverse(-18.918, -48.2772)
