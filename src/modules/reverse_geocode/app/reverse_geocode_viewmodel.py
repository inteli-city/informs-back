from src.shared.domain.entities.geocoded_address import GeocodedAddress
from src.shared.helpers.contracts.endpoints.reverse_geocode_contract import ReverseGeocodeResponseSchema


class ReverseGeocodeViewmodel:
    def __init__(self, address: GeocodedAddress):
        self.address = address

    def to_dict(self) -> dict:
        return ReverseGeocodeResponseSchema(
            street=self.address.street,
            number=self.address.number,
            city=self.address.city,
            formatted=self.address.formatted,
        ).model_dump()
