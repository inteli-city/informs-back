import pytest

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import PROFILE_ROLE
from src.shared.helpers.errors.domain_errors import EntityError


def _kwargs(**overrides):
    base = {
        "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120010",
        "role": PROFILE_ROLE.INSPECTOR,
        "name": "Inspector One",
        "email": "inspector@example.com",
        "system": "GAIA",
        "active": True,
        "created_at": 946684800000,
        "updated_at": 946684800000,
    }
    base.update(overrides)
    return base


class TestProfile:
    def test_valid_profile(self):
        profile = Profile(**_kwargs())
        assert profile.role == PROFILE_ROLE.INSPECTOR
        assert profile.active is True
        assert profile.vehicle_plate is None

    def test_invalid_user_id(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(user_id="too-short"))

    def test_invalid_role(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(role="ADMIN"))  # string, não enum

    def test_empty_name(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(name="   "))

    def test_invalid_email(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(email="not-an-email"))

    def test_empty_system(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(system=""))

    def test_active_must_be_bool(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(active="yes"))

    def test_vehicle_plate_optional(self):
        profile = Profile(**_kwargs(vehicle_plate="ABC1D23"))
        assert profile.vehicle_plate == "ABC1D23"

    def test_vehicle_plate_empty_invalid(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(vehicle_plate=""))

    def test_deactivate_marks_inactive_and_updates_timestamp(self):
        profile = Profile(**_kwargs())
        profile.deactivate(updated_at=999999999999)
        assert profile.active is False
        assert profile.updated_at == 999999999999

    def test_deactivate_rejects_non_int_timestamp(self):
        profile = Profile(**_kwargs())
        with pytest.raises(EntityError):
            profile.deactivate(updated_at="now")
