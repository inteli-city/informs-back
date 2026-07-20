import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.infra.dtos.profile_dynamo_dto import ProfileDynamoDTO


USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"


def _profile(**overrides) -> Profile:
    base = {
        "user_id": USER_ID,
        "role": ProfileRole.ADMIN,
        "name": "Admin",
        "email": "admin@example.com",
        "system": "GAIA",
        "active": True,
        "created_at": 946684800000,
        "updated_at": 946684800000,
        "vehicle_plate": None,
    }
    base.update(overrides)
    return Profile(**base)


class TestProfileDynamoDTO:
    def test_key_builders(self):
        assert ProfileDynamoDTO.build_pk(USER_ID) == f"user#{USER_ID}"
        assert ProfileDynamoDTO.build_sk() == "METADATA"
        assert ProfileDynamoDTO.build_gsi1_pk(ProfileRole.ADMIN) == "role#ADMIN"
        assert ProfileDynamoDTO.build_gsi1_sk("GAIA", USER_ID) == f"system#GAIA#user#{USER_ID}"

    def test_to_dynamo_contains_keys_and_gsi(self):
        item = ProfileDynamoDTO.from_entity(_profile(vehicle_plate="ABC1D23")).to_dynamo()

        assert item["role"] == "ADMIN"
        assert item["vehicle_plate"] == "ABC1D23"
        assert item["active"] is True
        assert item["GSI1PK"] == "role#ADMIN"
        assert item["GSI1SK"] == f"system#GAIA#user#{USER_ID}"

    def test_from_dynamo_round_trip(self):
        item = ProfileDynamoDTO.from_entity(_profile(role=ProfileRole.INSPECTOR)).to_dynamo()
        item["PK"] = ProfileDynamoDTO.build_pk(USER_ID)
        item["SK"] = ProfileDynamoDTO.build_sk()

        entity = ProfileDynamoDTO.from_dynamo(item).to_entity()

        assert entity.user_id == USER_ID
        assert entity.role == ProfileRole.INSPECTOR
        assert entity.email == "admin@example.com"
        assert entity.active is True

    def test_from_dynamo_invalid_pk_raises(self):
        item = ProfileDynamoDTO.from_entity(_profile()).to_dynamo()
        item["PK"] = "wrong-prefix"
        item["SK"] = "METADATA"

        with pytest.raises(KeyError):
            ProfileDynamoDTO.from_dynamo(item)
