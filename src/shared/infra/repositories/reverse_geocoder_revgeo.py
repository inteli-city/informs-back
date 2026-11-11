import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from src.shared.domain.entities.geocoded_address import GeocodedAddress
from src.shared.domain.repositories.reverse_geocoder_interface import IReverseGeocoder
from src.shared.environments import Environments
from src.shared.helpers.errors.usecase_errors import ReverseGeocodeUnavailable


NOMINATIM_PATH = "/api/geocode/nominatim"

# Ordem de preferência do Nominatim para "cidade": município pequeno vem como
# `town`/`village`, e às vezes só como `municipality`.
_CITY_KEYS = ("city", "town", "village", "municipality", "city_district", "county")
_STREET_KEYS = ("road", "pedestrian", "footway", "residential", "path")


def _pick(address: dict, keys) -> str:
    for key in keys:
        value = address.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def parse_nominatim(result: Any) -> Optional[GeocodedAddress]:
    """Lê o `result` do wrapper (resposta `jsonv2` do Nominatim). Sem endereço
    (`{"error": "Unable to geocode"}`, ponto no mar...): `None`."""
    if isinstance(result, list):
        result = result[0] if result else None
    if not isinstance(result, dict) or result.get("error"):
        return None
    address = result.get("address")
    if not isinstance(address, dict):
        return None

    geocoded = GeocodedAddress(
        street=_pick(address, _STREET_KEYS),
        number=_pick(address, ("house_number",)),
        city=_pick(address, _CITY_KEYS),
        formatted=result.get("display_name", "").strip() if isinstance(result.get("display_name"), str) else "",
    )
    return geocoded if geocoded.street or geocoded.city else None


class ReverseGeocoderRevgeo(IReverseGeocoder):
    """Geocodificação reversa pelo wrapper `revgeo` da Intelicity, provider
    Nominatim. A chave (`X-API-Key`) fica só no back-end: o app chama esta
    API, nunca o wrapper direto."""

    def __init__(self):
        envs = Environments.get_envs()
        self.base_url = (envs.revgeo_base_url or "").rstrip("/")
        self.api_key = envs.revgeo_api_key
        self.timeout = envs.revgeo_timeout

    def reverse(self, latitude: float, longitude: float) -> Optional[GeocodedAddress]:
        if not self.base_url or not self.api_key:
            raise ReverseGeocodeUnavailable("Serviço de endereço não configurado")

        query = urllib.parse.urlencode({
            "lat": latitude,
            "lng": longitude,
            "addressdetails": "true",
            "accept-language": "pt-BR",
            "zoom": 18,
        })
        request = urllib.request.Request(f"{self.base_url}{NOMINATIM_PATH}?{query}", method="GET")
        request.add_header("X-API-Key", self.api_key)
        request.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            logging.getLogger(__name__).warning("revgeo respondeu %s", err.code)
            raise ReverseGeocodeUnavailable() from err
        except (urllib.error.URLError, TimeoutError, ValueError) as err:
            logging.getLogger(__name__).warning("revgeo indisponível: %s", err)
            raise ReverseGeocodeUnavailable() from err

        if not isinstance(body, dict) or "result" not in body:
            raise ReverseGeocodeUnavailable("Resposta inesperada do serviço de endereço")
        return parse_nominatim(body["result"])
