import pytest

from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID, SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.errors.domain_errors import EntityError


def _role(**overrides):
    base = {
        "system": "GAIA",
        "name": "Gestor",
        "actions": [Action.FORMS_ASSIGN],
        "created_at": 1,
        "updated_at": 1,
    }
    base.update(overrides)
    return SystemRole(**base)


class TestSystemRole:
    def test_valid_role_gets_generated_id(self):
        role = _role()
        assert role.role_id
        assert role.is_default is False
        assert role.actions == [Action.FORMS_ASSIGN]

    def test_name_is_trimmed(self):
        assert _role(name="  Fiscal  ").name == "Fiscal"

    def test_duplicated_actions_are_collapsed(self):
        assert _role(actions=[Action.FORMS_ASSIGN, Action.FORMS_ASSIGN]).actions == [Action.FORMS_ASSIGN]

    def test_empty_actions_are_allowed(self):
        assert _role(actions=[]).actions == []

    def test_admin_id_is_reserved(self):
        with pytest.raises(EntityError):
            _role(role_id=ADMIN_ROLE_ID)

    def test_admin_name_is_reserved(self):
        with pytest.raises(EntityError):
            _role(name="administrador")

    def test_unknown_action_is_rejected(self):
        with pytest.raises(EntityError):
            _role(actions=["forms.assign"])

    def test_long_name_is_rejected(self):
        with pytest.raises(EntityError):
            _role(name="x" * 41)


class TestSystemMembership:
    def test_valid_membership(self):
        membership = SystemMembership(user_id="u1", system="GAIA", role_id="r1", created_at=1, updated_at=1)
        assert membership.role_id == "r1"

    def test_empty_role_is_rejected(self):
        with pytest.raises(EntityError):
            SystemMembership(user_id="u1", system="GAIA", role_id="", created_at=1, updated_at=1)
