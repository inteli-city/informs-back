from typing import cast

import pytest

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.helpers.errors.domain_errors import EntityError


def _kwargs(**overrides):
    base = {
        "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120010",
        "role": ProfileRole.INSPECTOR,
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
        assert profile.role == ProfileRole.INSPECTOR
        assert profile.active is True
        assert profile.vehicle_plate is None

    def test_invalid_user_id(self):
        kwargs = _kwargs(user_id="too-short")
        with pytest.raises(EntityError):
            Profile(**kwargs)

    def test_invalid_role(self):
        # cast esquiva o type checker: passamos string de propósito
        # para validar a checagem em runtime.
        kwargs = _kwargs(role=cast(ProfileRole, "ADMIN"))
        with pytest.raises(EntityError):
            Profile(**kwargs)

    def test_empty_name(self):
        kwargs = _kwargs(name="   ")
        with pytest.raises(EntityError):
            Profile(**kwargs)

    def test_invalid_email(self):
        kwargs = _kwargs(email="not-an-email")
        with pytest.raises(EntityError):
            Profile(**kwargs)

    def test_empty_system(self):
        kwargs = _kwargs(system="")
        with pytest.raises(EntityError):
            Profile(**kwargs)

    def test_active_must_be_bool(self):
        kwargs = _kwargs(active=cast(bool, "yes"))
        with pytest.raises(EntityError):
            Profile(**kwargs)

    def test_vehicle_plate_optional(self):
        profile = Profile(**_kwargs(vehicle_plate="ABC1D23"))
        assert profile.vehicle_plate == "ABC1D23"

    def test_vehicle_plate_empty_invalid(self):
        kwargs = _kwargs(vehicle_plate="")
        with pytest.raises(EntityError):
            Profile(**kwargs)

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


class TestProfileScope:
    """Especificação Uberlândia §7: `scope` vazio = sem restrição (comportamento atual)."""

    def test_scope_defaults_to_empty_dict(self):
        profile = Profile(**_kwargs())
        assert profile.scope == {}

    def test_scope_accepts_custom_value(self):
        profile = Profile(**_kwargs(scope={"bairro": ["Santa Mônica", "Tibery"]}))
        assert profile.scope == {"bairro": ["Santa Mônica", "Tibery"]}

    def test_scope_rejects_malformed_value(self):
        with pytest.raises(EntityError):
            Profile(**_kwargs(scope={"bairro": "Santa Mônica"}))

    def test_manager_and_supervisor_roles_are_valid(self):
        assert Profile(**_kwargs(role=ProfileRole.MANAGER)).role == ProfileRole.MANAGER
        assert Profile(**_kwargs(role=ProfileRole.SUPERVISOR)).role == ProfileRole.SUPERVISOR
