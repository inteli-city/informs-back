import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.infra.dtos.profile_dynamo_dto import ProfileDynamoDTO
from src.shared.infra.dtos.system_membership_dynamo_dto import SystemMembershipDynamoDTO
from src.shared.infra.dtos.system_role_dynamo_dto import SystemRoleDynamoDTO


USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"


def _profile(**overrides) -> Profile:
    base = {
        "user_id": USER_ID,
        "name": "Admin",
        "email": "admin@example.com",
        "active": True,
        "created_at": 946684800000,
        "updated_at": 946684800000,
    }
    base.update(overrides)
    return Profile(**base)


class TestProfileDynamoDTO:
    def test_key_builders(self):
        assert ProfileDynamoDTO.build_pk(USER_ID) == f"user#{USER_ID}"
        assert ProfileDynamoDTO.build_sk() == "METADATA"

    def test_super_admin_goes_to_the_sparse_index(self):
        item = ProfileDynamoDTO.from_entity(_profile(super_admin=True)).to_dynamo()

        assert item["super_admin"] is True
        assert item["GSI1PK"] == "super_admin"
        assert item["GSI1SK"] == f"user#{USER_ID}"

    def test_regular_person_stays_out_of_the_index(self):
        item = ProfileDynamoDTO.from_entity(_profile()).to_dynamo()

        assert item["super_admin"] is False
        assert "GSI1PK" not in item
        assert "GSI1SK" not in item

    def test_from_dynamo_round_trip(self):
        item = ProfileDynamoDTO.from_entity(_profile(super_admin=True)).to_dynamo()
        item["PK"] = ProfileDynamoDTO.build_pk(USER_ID)
        item["SK"] = ProfileDynamoDTO.build_sk()

        entity = ProfileDynamoDTO.from_dynamo(item).to_entity()

        assert entity.user_id == USER_ID
        assert entity.super_admin is True
        assert entity.email == "admin@example.com"
        assert entity.active is True

    def test_from_dynamo_reads_legacy_item_without_super_admin(self):
        # Item de antes da migração: tem role/system e não tem super_admin.
        item = {
            "PK": f"user#{USER_ID}", "SK": "METADATA", "name": "Admin", "email": "admin@example.com",
            "active": True, "created_at": 1, "updated_at": 1, "role": "ADMIN", "system": "GAIA",
        }

        entity = ProfileDynamoDTO.from_dynamo(item).to_entity()

        assert entity.super_admin is False

    def test_from_dynamo_invalid_pk_raises(self):
        item = ProfileDynamoDTO.from_entity(_profile()).to_dynamo()
        item["PK"] = "wrong-prefix"
        item["SK"] = "METADATA"

        with pytest.raises(KeyError):
            ProfileDynamoDTO.from_dynamo(item)


class TestSystemMembershipDynamoDTO:
    def test_item_is_indexed_by_system_and_role(self):
        membership = SystemMembership(user_id=USER_ID, system="GAIA", role_id="r1", created_at=1, updated_at=2)

        item = SystemMembershipDynamoDTO.from_entity(membership).to_dynamo()

        assert SystemMembershipDynamoDTO.build_pk(USER_ID) == f"user#{USER_ID}"
        assert SystemMembershipDynamoDTO.build_sk("GAIA") == "system#GAIA"
        assert item["GSI1PK"] == "system#GAIA"
        assert item["GSI1SK"] == f"role#r1#user#{USER_ID}"

    def test_round_trip(self):
        membership = SystemMembership(user_id=USER_ID, system="GAIA", role_id="r1", created_at=1, updated_at=2)

        entity = SystemMembershipDynamoDTO.from_dynamo(
            SystemMembershipDynamoDTO.from_entity(membership).to_dynamo()
        ).to_entity()

        assert (entity.user_id, entity.system, entity.role_id, entity.updated_at) == (USER_ID, "GAIA", "r1", 2)


class TestSystemRoleDynamoDTO:
    def test_round_trip(self):
        role = SystemRole(
            system="GAIA", role_id="r1", name="Gestor", actions=[Action.FORMS_ASSIGN, Action.FORMS_RELEASE],
            is_default=True, created_at=1, updated_at=2,
        )

        item = SystemRoleDynamoDTO.from_entity(role).to_dynamo()
        entity = SystemRoleDynamoDTO.from_dynamo(item).to_entity()

        assert SystemRoleDynamoDTO.build_pk("GAIA") == "system#GAIA"
        assert SystemRoleDynamoDTO.build_sk("r1") == "role#r1"
        assert item["actions"] == ["forms.assign", "forms.release"]
        assert entity.actions == [Action.FORMS_ASSIGN, Action.FORMS_RELEASE]
        assert entity.is_default is True

    def test_action_removed_from_catalog_is_ignored(self):
        item = {
            "system": "GAIA", "role_id": "r1", "name": "Gestor", "actions": ["forms.assign", "forms.gone"],
            "is_default": False, "created_at": 1, "updated_at": 1,
        }

        assert SystemRoleDynamoDTO.from_dynamo(item).to_entity().actions == [Action.FORMS_ASSIGN]
