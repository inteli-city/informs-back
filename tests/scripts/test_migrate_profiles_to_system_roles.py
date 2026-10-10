"""Migração do role global para roles por sistema, contra uma tabela em
memória que imita o boto3 (scan, get_item, put_item, update_item)."""

import argparse
import importlib.util
from pathlib import Path

import pytest

from src.shared.infra.dtos.profile_dynamo_dto import ProfileDynamoDTO
from src.shared.infra.dtos.system_membership_dynamo_dto import SystemMembershipDynamoDTO
from src.shared.infra.dtos.system_role_dynamo_dto import SystemRoleDynamoDTO


_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "migrate_profiles_to_system_roles.py"
_spec = importlib.util.spec_from_file_location("migrate_profiles_to_system_roles", _SCRIPT)
migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migration)


U_ADMIN = "00000000-0000-0000-0000-0000000000a1"
U_TECNICO = "00000000-0000-0000-0000-0000000000a2"
U_GESTOR = "00000000-0000-0000-0000-0000000000a3"
U_FISCAL = "00000000-0000-0000-0000-0000000000a4"


class FakeTable:
    def __init__(self, items):
        self.items = {(item["PK"], item["SK"]): dict(item) for item in items}

    def scan(self, FilterExpression=None, **kwargs):
        return {"Items": [dict(item) for (_, sk), item in self.items.items() if sk == "METADATA"]}

    def get_item(self, Key):
        item = self.items.get((Key["PK"], Key["SK"]))
        return {"Item": dict(item)} if item else {}

    def put_item(self, Item):
        self.items[(Item["PK"], Item["SK"])] = dict(Item)

    def update_item(self, Key, UpdateExpression, ExpressionAttributeNames, ExpressionAttributeValues):
        item = self.items[(Key["PK"], Key["SK"])]
        set_part, _, remove_part = UpdateExpression.partition(" REMOVE ")
        for assignment in set_part.removeprefix("SET ").split(", "):
            name, value = assignment.split(" = ")
            item[ExpressionAttributeNames[name]] = ExpressionAttributeValues[value]
        for name in filter(None, remove_part.split(", ")):
            item.pop(ExpressionAttributeNames[name], None)

    def get(self, pk, sk):
        return self.items.get((pk, sk))


def _legacy_person(user_id, role, system):
    return {
        "PK": f"user#{user_id}", "SK": "METADATA", "user_id": user_id, "name": "X", "email": "x@example.com",
        "active": True, "created_at": 1, "updated_at": 1, "role": role, "system": system,
        "scope": {}, "vehicle_plate": None, "GSI1PK": f"role#{role}", "GSI1SK": f"system#{system}#user#{user_id}",
    }


def _table():
    return FakeTable([
        _legacy_person(U_ADMIN, "ADMIN", "GAIA"),
        _legacy_person(U_TECNICO, "INSPECTOR", "GAIA"),
        _legacy_person(U_GESTOR, "MANAGER", "UBERLANDIA"),
        _legacy_person(U_FISCAL, "SUPERVISOR", "UBERLANDIA"),
    ])


class TestMigrateProfilesToSystemRoles:
    def test_creates_roles_per_system(self):
        table = _table()
        migration.migrate(table, super_admins=set(), extra_systems=[], dry_run=False)

        assert table.get("system#GAIA", "role#tecnico")["is_default"] is True
        assert table.get("system#GAIA", "role#gestor") is None
        assert table.get("system#UBERLANDIA", "role#tecnico")["is_default"] is True
        assert table.get("system#UBERLANDIA", "role#gestor")["actions"] == ["forms.view_all", "forms.assign", "forms.release"]
        assert table.get("system#UBERLANDIA", "role#fiscal") is not None

    def test_creates_memberships_from_the_old_role(self):
        table = _table()
        migration.migrate(table, super_admins=set(), extra_systems=[], dry_run=False)

        assert table.get(f"user#{U_ADMIN}", "system#GAIA")["role_id"] == "ADMIN"
        assert table.get(f"user#{U_TECNICO}", "system#GAIA")["role_id"] == "tecnico"
        assert table.get(f"user#{U_GESTOR}", "system#UBERLANDIA")["role_id"] == "gestor"
        membership = table.get(f"user#{U_FISCAL}", "system#UBERLANDIA")
        assert membership["GSI1PK"] == "system#UBERLANDIA"
        assert membership["GSI1SK"] == f"role#fiscal#user#{U_FISCAL}"

    def test_cleans_the_person_and_marks_super_admins(self):
        table = _table()
        migration.migrate(table, super_admins={U_ADMIN}, extra_systems=[], dry_run=False)

        admin = table.get(f"user#{U_ADMIN}", "METADATA")
        assert admin["super_admin"] is True
        assert (admin["GSI1PK"], admin["GSI1SK"]) == ("super_admin", f"user#{U_ADMIN}")
        for field in ("role", "system", "scope", "vehicle_plate"):
            assert field not in admin

        tecnico = table.get(f"user#{U_TECNICO}", "METADATA")
        assert tecnico["super_admin"] is False
        assert "GSI1PK" not in tecnico and "GSI1SK" not in tecnico

    def test_migrated_items_are_read_by_the_new_dtos(self):
        table = _table()
        migration.migrate(table, super_admins={U_ADMIN}, extra_systems=[], dry_run=False)

        assert ProfileDynamoDTO.from_dynamo(table.get(f"user#{U_ADMIN}", "METADATA")).to_entity().super_admin is True
        assert SystemMembershipDynamoDTO.from_dynamo(table.get(f"user#{U_GESTOR}", "system#UBERLANDIA")).to_entity().role_id == "gestor"
        assert SystemRoleDynamoDTO.from_dynamo(table.get("system#GAIA", "role#tecnico")).to_entity().name == "Técnico"

    def test_running_twice_changes_nothing(self):
        table = _table()
        migration.migrate(table, super_admins={U_ADMIN}, extra_systems=[], dry_run=False)
        snapshot = {key: dict(item) for key, item in table.items.items()}

        migration.migrate(table, super_admins={U_ADMIN}, extra_systems=[], dry_run=False)

        assert table.items == snapshot

    def test_extra_system_gets_the_default_role(self):
        table = _table()
        migration.migrate(table, super_admins=set(), extra_systems=["SGC"], dry_run=False)
        assert table.get("system#SGC", "role#tecnico")["is_default"] is True

    def test_dry_run_writes_nothing(self):
        table = _table()
        before = {key: dict(item) for key, item in table.items.items()}

        migration.migrate(table, super_admins={U_ADMIN}, extra_systems=[], dry_run=True)

        assert table.items == before


class TestSystemAdminOption:
    """--system-admin: ADMIN no sistema pedido, mesmo que o `system` gravado
    no perfil seja outro (ex.: conta de integração que cria OS em UBERLANDIA)."""

    def test_old_admin_also_becomes_admin_of_the_requested_system(self):
        table = _table()
        migration.migrate(table, set(), [], dry_run=False, system_admins=[(U_ADMIN, "UBERLANDIA")])

        assert table.get(f"user#{U_ADMIN}", "system#GAIA")["role_id"] == "ADMIN"
        membership = table.get(f"user#{U_ADMIN}", "system#UBERLANDIA")
        assert membership["role_id"] == "ADMIN"
        assert membership["GSI1SK"] == f"role#ADMIN#user#{U_ADMIN}"

    def test_replaces_the_role_already_in_the_system(self):
        table = _table()
        migration.migrate(table, set(), [], dry_run=False, system_admins=[(U_GESTOR, "UBERLANDIA")])

        membership = table.get(f"user#{U_GESTOR}", "system#UBERLANDIA")
        assert membership["role_id"] == "ADMIN"
        assert membership["GSI1SK"] == f"role#ADMIN#user#{U_GESTOR}"

    def test_person_without_profile_is_skipped(self):
        table = _table()
        ghost = "00000000-0000-0000-0000-0000000000ff"
        migration.migrate(table, set(), [], dry_run=False, system_admins=[(ghost, "UBERLANDIA")])

        assert table.get(f"user#{ghost}", "system#UBERLANDIA") is None

    def test_running_twice_changes_nothing(self):
        table = _table()
        migration.migrate(table, set(), [], dry_run=False, system_admins=[(U_ADMIN, "UBERLANDIA")])
        snapshot = {key: dict(item) for key, item in table.items.items()}

        migration.migrate(table, set(), [], dry_run=False, system_admins=[(U_ADMIN, "UBERLANDIA")])

        assert table.items == snapshot

    def test_option_format_is_validated(self):
        assert migration._parse_system_admin(f"{U_ADMIN}:UBERLANDIA") == (U_ADMIN, "UBERLANDIA")
        for invalid in ("sem-dois-pontos", ":UBERLANDIA", f"{U_ADMIN}:"):
            with pytest.raises(argparse.ArgumentTypeError):
                migration._parse_system_admin(invalid)
