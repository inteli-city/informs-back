"""Para quem se cria formulário: cada destino ligado no papel (Admin → Papéis)."""

from copy import deepcopy

import pytest

from src.modules.create_form.app.create_form_usecase import CreateFormUsecase
from src.modules.get_system_assignees.app.get_system_assignees_controller import GetSystemAssigneesController
from src.modules.get_system_assignees.app.get_system_assignees_usecase import GetSystemAssigneesUsecase
from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.enums.assignment_option_enum import AssignmentOption as Opt
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.dtos.system_role_dynamo_dto import SystemRoleDynamoDTO
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.profile_repository_mock import MOCK_INSPECTOR_ID, ProfileRepositoryMock
from src.shared.infra.repositories.system_config_repository_mock import SystemConfigRepositoryMock
from src.shared.infra.repositories.system_group_repository_mock import MOCK_GROUP_A_ID, SystemGroupRepositoryMock
from src.shared.infra.repositories.system_role_repository_mock import MOCK_TECNICO_ROLE_ID, SystemRoleRepositoryMock
from tests.modules.access_fixtures import requester_user
from tests.modules.create_form.app.test_create_form_usecase import _make_usecase_and_payload


CREATOR = MOCK_INSPECTOR_ID
COLLEAGUE = "d61dbf66-a10f-11ed-a8fc-0242ac120055"
OUTSIDER = "d61dbf66-a10f-11ed-a8fc-0242ac120056"


class Scenario:
    def __init__(self, options, default=Opt.SELF, allow_open=True, allow_unassigned=True):
        self.profile_repo = ProfileRepositoryMock()
        self.role_repo = SystemRoleRepositoryMock()
        self.group_repo = SystemGroupRepositoryMock()
        self.config_repo = SystemConfigRepositoryMock()
        self.config_repo.put(SystemConfig(
            system="GAIA", created_at=1, updated_at=1, allow_unassigned_forms=allow_unassigned,
            app_config={"creation": {"allow_open": allow_open}},
        ))
        # O Técnico (papel do inspetor no GAIA) com as opções do teste.
        self.role_repo.put_role(SystemRole(
            system="GAIA", role_id=MOCK_TECNICO_ROLE_ID, name="Técnico",
            actions=[Action.FORMS_CREATE, Action.TRACKING_START], created_at=1, updated_at=1,
            assignment_options=options, default_assignment=default,
        ))
        for user_id, name in ((COLLEAGUE, "Bruno Colega"), (OUTSIDER, "Fora do Sistema")):
            self.profile_repo.create(Profile(
                user_id=user_id, name=name, email=f"{user_id[-4:]}@example.com", active=True,
                created_at=1, updated_at=1,
            ))
        self.profile_repo.put_membership(SystemMembership(
            user_id=COLLEAGUE, system="GAIA", role_id=MOCK_TECNICO_ROLE_ID, created_at=1, updated_at=1,
            groups=[MOCK_GROUP_A_ID],
        ))
        self.access_control = AccessControl(self.profile_repo, self.role_repo)
        self.usecase = CreateFormUsecase(
            FormRepositoryMock(), FileRepositoryMock(),
            system_config_repo=self.config_repo, access_control=self.access_control, group_repo=self.group_repo,
        )

    def create(self, user_id, groups=None):
        _, payload, _ = _make_usecase_and_payload()
        payload = deepcopy(payload)
        payload.update(created_by=CREATOR, user_id=user_id, groups=groups)
        form, _ = self.usecase(**payload)
        return form


# --- Papel ---------------------------------------------------------------------

def test_role_defaults_keep_previous_behaviour():
    role = SystemRole(system="GAIA", name="X", actions=[], created_at=1, updated_at=1)
    assert role.assignment_options == [Opt.SELF, Opt.OPEN]
    assert role.default_assignment is Opt.SELF


def test_role_needs_an_option_and_a_default_among_them():
    with pytest.raises(EntityError):
        SystemRole(system="GAIA", name="X", actions=[], created_at=1, updated_at=1, assignment_options=[])
    with pytest.raises(EntityError):
        SystemRole(
            system="GAIA", name="X", actions=[], created_at=1, updated_at=1,
            assignment_options=[Opt.SELF], default_assignment=Opt.OPEN,
        )


def test_dto_round_trip_and_legacy_items():
    role = SystemRole(
        system="GAIA", name="X", actions=[], created_at=1, updated_at=1,
        assignment_options=[Opt.OPEN, Opt.TARGETED], default_assignment=Opt.TARGETED,
    )
    item = SystemRoleDynamoDTO.from_entity(role).to_dynamo()
    assert item["assignment_options"] == ["targeted", "open"]
    back = SystemRoleDynamoDTO.from_dynamo(item).to_entity()
    assert back.assignment_options == [Opt.TARGETED, Opt.OPEN]
    assert back.default_assignment is Opt.TARGETED

    del item["assignment_options"], item["default_assignment"]
    legacy = SystemRoleDynamoDTO.from_dynamo(item).to_entity()
    assert legacy.assignment_options == [Opt.SELF, Opt.OPEN]
    assert legacy.default_assignment is Opt.SELF


# --- Criação -------------------------------------------------------------------

def test_self_needs_the_self_option():
    assert Scenario([Opt.SELF]).create(CREATOR).user_id == CREATOR
    only_open = Scenario([Opt.OPEN], default=Opt.OPEN)
    with pytest.raises(ForbiddenAction):
        only_open.create(CREATOR)


def test_open_needs_the_option_and_the_system_flag():
    assert Scenario([Opt.OPEN], default=Opt.OPEN).create(None).user_id is None
    only_self = Scenario([Opt.SELF])
    with pytest.raises(ForbiddenAction):
        only_self.create(None)
    system_closed = Scenario([Opt.OPEN], default=Opt.OPEN, allow_open=False)
    with pytest.raises(ForbiddenAction):
        system_closed.create(None)


def test_targeted_person_goes_straight_to_them():
    form = Scenario([Opt.TARGETED], default=Opt.TARGETED).create(COLLEAGUE)
    assert form.user_id == COLLEAGUE


def test_targeted_group_only_stays_in_the_group_pool_even_without_allow_open():
    form = Scenario([Opt.TARGETED], default=Opt.TARGETED, allow_open=False).create(None, groups=[MOCK_GROUP_A_ID])
    assert form.user_id is None
    assert form.groups == [MOCK_GROUP_A_ID]


def test_targeted_needs_the_option():
    scenario = Scenario([Opt.SELF, Opt.OPEN])
    with pytest.raises(ForbiddenAction):
        scenario.create(COLLEAGUE)
    with pytest.raises(ForbiddenAction):
        scenario.create(None, groups=[MOCK_GROUP_A_ID])


def test_targeted_person_must_belong_to_the_system():
    scenario = Scenario([Opt.TARGETED], default=Opt.TARGETED)
    with pytest.raises(NoItemsFound):
        scenario.create(OUTSIDER)


# --- Grupos e pessoas para escolher ---------------------------------------------

def test_assignees_list_groups_and_active_members_without_the_requester():
    scenario = Scenario([Opt.SELF, Opt.TARGETED], allow_unassigned=False)
    usecase = GetSystemAssigneesUsecase(
        scenario.access_control, scenario.profile_repo, scenario.group_repo, scenario.config_repo,
    )

    result = usecase(CREATOR, "GAIA")

    assert [user.membership.user_id for user in result.users] == [COLLEAGUE]
    assert [group.group_id for group in result.groups]
    assert result.allows_group_only is False


def test_assignees_endpoint_needs_the_targeted_option():
    scenario = Scenario([Opt.SELF])
    controller = GetSystemAssigneesController(GetSystemAssigneesUsecase(
        scenario.access_control, scenario.profile_repo, scenario.group_repo, scenario.config_repo,
    ))
    request = HttpRequest(body={"requester_user": requester_user(CREATOR), "system": "GAIA"})

    assert controller(request).status_code == 403

    scenario.role_repo.put_role(SystemRole(
        system="GAIA", role_id=MOCK_TECNICO_ROLE_ID, name="Técnico", actions=[Action.FORMS_CREATE],
        created_at=1, updated_at=1, assignment_options=[Opt.TARGETED], default_assignment=Opt.TARGETED,
    ))
    response = controller(request)
    assert response.status_code == 200
    assert response.body["users"] == [{"user_id": COLLEAGUE, "name": "Bruno Colega", "groups": [MOCK_GROUP_A_ID]}]
    assert "email" not in response.body["users"][0]


def test_assignees_skip_inactive_members_and_need_a_config_to_allow_group_only():
    scenario = Scenario([Opt.TARGETED], default=Opt.TARGETED, allow_unassigned=True)
    inactive = "d61dbf66-a10f-11ed-a8fc-0242ac120057"
    scenario.profile_repo.create(Profile(
        user_id=inactive, name="Inativo", email="inativo@example.com", active=False, created_at=1, updated_at=1,
    ))
    scenario.profile_repo.put_membership(SystemMembership(
        user_id=inactive, system="GAIA", role_id=MOCK_TECNICO_ROLE_ID, created_at=1, updated_at=1,
    ))
    usecase = GetSystemAssigneesUsecase(scenario.access_control, scenario.profile_repo, scenario.group_repo, None)

    result = usecase(CREATOR, "GAIA")

    assert [user.membership.user_id for user in result.users] == [COLLEAGUE]
    assert result.allows_group_only is False
