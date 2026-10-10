from typing import cast

import pytest

from src.shared.domain.entities.profile import Profile
from src.shared.helpers.errors.domain_errors import EntityError


def _kwargs(**overrides):
    base = {
        "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120010",
        "name": "Inspector One",
        "email": "inspector@example.com",
        "active": True,
        "created_at": 946684800000,
        "updated_at": 946684800000,
    }
    base.update(overrides)
    return base


class TestProfile:
    def test_valid_profile(self):
        profile = Profile(**_kwargs())
        assert profile.active is True
        assert profile.super_admin is False

    def test_invalid_user_id(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(user_id="too-short"))

    def test_empty_name(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(name="   "))

    def test_invalid_email(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(email="not-an-email"))

    def test_active_must_be_bool(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(active=cast(bool, "yes")))

    def test_super_admin_must_be_bool(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(super_admin=cast(bool, "yes")))

    def test_is_active_super_admin(self):
        assert Profile(**_kwargs(super_admin=True)).is_active_super_admin() is True
        assert Profile(**_kwargs(super_admin=True, active=False)).is_active_super_admin() is False
        assert Profile(**_kwargs()).is_active_super_admin() is False

    def test_deactivate_marks_inactive_and_updates_timestamp(self):
        profile = Profile(**_kwargs())
        profile.deactivate(updated_at=999999999999)
        assert profile.active is False
        assert profile.updated_at == 999999999999

    def test_deactivate_rejects_non_int_timestamp(self):
        profile = Profile(**_kwargs())
        # cast esquiva o type checker: passamos string de propósito para
        # validar a checagem em runtime (rule python:S5655 falso-positiva).
        bad_timestamp = cast(int, "now")
        with pytest.raises(EntityError):
            profile.deactivate(updated_at=bad_timestamp)
