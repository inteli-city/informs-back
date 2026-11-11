import importlib
import json
import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.modules.reverse_geocode.app.reverse_geocode_controller import ReverseGeocodeController
from src.modules.reverse_geocode.app.reverse_geocode_usecase import ReverseGeocodeUsecase
from src.shared.domain.repositories.reverse_geocoder_interface import IReverseGeocoder
from src.shared.helpers.errors.usecase_errors import NoItemsFound, ReverseGeocodeUnavailable
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.reverse_geocoder_mock import ReverseGeocoderMock

REQUESTER = {
    "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120002",
    "name": "Técnico",
    "email": "tecnico@example.com",
    "cognito:groups": "FORMULARIOS,GAIA",
}


class UnavailableGeocoder(IReverseGeocoder):
    def reverse(self, latitude, longitude):
        raise ReverseGeocodeUnavailable()


def _controller(geocoder=None):
    return ReverseGeocodeController(ReverseGeocodeUsecase(geocoder or ReverseGeocoderMock()))


class TestReverseGeocodeUsecase:
    def test_returns_the_address(self):
        address = ReverseGeocodeUsecase(ReverseGeocoderMock())(-18.918, -48.2772)
        assert address.street == "Avenida João Naves de Ávila"

    def test_point_without_address_raises_not_found(self):
        with pytest.raises(NoItemsFound):
            ReverseGeocodeUsecase(ReverseGeocoderMock())(0.0, 0.0)


class TestReverseGeocodeController:
    def test_ok(self):
        response = _controller()(HttpRequest(query_params={"lat": "-18.918", "lng": "-48.2772"}, body={"requester_user": REQUESTER}))

        assert response.status_code == 200
        assert response.body == {
            "street": "Avenida João Naves de Ávila",
            "number": "2121",
            "city": "Uberlândia",
            "formatted": "Avenida João Naves de Ávila, 2121, Santa Mônica, Uberlândia, Minas Gerais, Brasil",
        }

    def test_without_address_is_404(self):
        response = _controller()(HttpRequest(query_params={"lat": "0", "lng": "0"}, body={"requester_user": REQUESTER}))
        assert response.status_code == 404

    @pytest.mark.parametrize("query", [{"lat": "-18.9"}, {"lat": "91", "lng": "0"}, {"lat": "x", "lng": "0"}])
    def test_invalid_point_is_400(self, query):
        response = _controller()(HttpRequest(query_params=query, body={"requester_user": REQUESTER}))
        assert response.status_code == 400

    def test_service_down_is_502(self):
        response = _controller(UnavailableGeocoder())(
            HttpRequest(query_params={"lat": "-18.918", "lng": "-48.2772"}, body={"requester_user": REQUESTER})
        )
        assert response.status_code == 502


class TestReverseGeocodePresenter:
    def test_lambda_handler(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.reverse_geocode.app import reverse_geocode_presenter

        importlib.reload(reverse_geocode_presenter)
        event = {
            "rawPath": "/mss-formularios/geocode/reverse",
            "queryStringParameters": {"lat": "-18.918", "lng": "-48.2772"},
            "requestContext": {"authorizer": {"claims": REQUESTER}},
        }

        response = reverse_geocode_presenter.lambda_handler(event, None)

        assert response["statusCode"] == 200
        assert json.loads(response["body"])["city"] == "Uberlândia"
