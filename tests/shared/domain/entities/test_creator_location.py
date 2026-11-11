import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.shared.domain.entities.creator_location import CreatorLocation
from src.shared.helpers.errors.domain_errors import EntityError


class TestCreatorLocation:
    def test_keeps_all_fields(self):
        location = CreatorLocation(latitude=-18.9, longitude=-48.27, accuracy=12, captured_at=1715000000000)

        assert location.to_dict() == {
            "latitude": -18.9, "longitude": -48.27, "accuracy": 12.0, "captured_at": 1715000000000,
        }

    def test_accuracy_and_captured_at_are_optional(self):
        location = CreatorLocation(latitude=0, longitude=0)

        assert location.accuracy is None
        assert location.captured_at is None

    @pytest.mark.parametrize("kwargs", [
        {"latitude": 91, "longitude": 0},
        {"latitude": 0, "longitude": -181},
        {"latitude": "1", "longitude": 0},
        {"latitude": True, "longitude": 0},
        {"latitude": 0, "longitude": 0, "accuracy": -1},
        {"latitude": 0, "longitude": 0, "captured_at": 1.5},
        {"latitude": 0, "longitude": 0, "captured_at": -1},
    ])
    def test_rejects_invalid_values(self, kwargs):
        with pytest.raises(EntityError):
            CreatorLocation(**kwargs)

    def test_from_dict_accepts_dynamo_decimals(self):
        from decimal import Decimal

        location = CreatorLocation.from_dict({
            "latitude": Decimal("-18.9"), "longitude": Decimal("-48.27"),
            "accuracy": Decimal("5.5"), "captured_at": Decimal("1715000000000"),
        })

        assert location == CreatorLocation(-18.9, -48.27, 5.5, 1715000000000)
