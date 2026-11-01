"""Evidência do IN-1.1 (planejamento 2027) e da ADR-0022.

Uberlândia com o grupo A (usuários 1 a 5) e o B (6 a 10):
  - formulário com `groups: [A]` aparece só para 1 a 5;
  - com `user_id` do usuário 2, só para o 2;
  - sem nenhum dos dois, para os 10.

Cobre os três caminhos até uma OS aberta: o pool (GET /forms?scope=pool), a
ficha (GET /forms/{id}) e o claim (POST /forms/{id}/claim).
"""

import pytest

from src.modules.claim_form.app.claim_form_usecase import ClaimFormUsecase
from src.modules.get_all_forms.app.get_all_forms_usecase import GetAllFormsUsecase
from src.modules.get_form.app.get_form_usecase import GetFormUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.infra.dtos.user_gateway import UserGatewayDTO
from src.shared.infra.repositories.form_event_repository_mock import FormEventRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.system_role_repository_mock import SystemRoleRepositoryMock

SYSTEM = "UBERLANDIA"
GROUP_A = "equipe-a"
GROUP_B = "equipe-b"
USERS = {n: f"00000000-0000-4000-8000-{n:012d}" for n in range(1, 11)}
MANAGER_ID = "00000000-0000-4000-8000-000000000099"
FORM_GROUP_A = "10000000-0000-4000-8000-00000000000a"
FORM_USER_2 = "10000000-0000-4000-8000-000000000002"
FORM_EVERYONE = "10000000-0000-4000-8000-0000000000ff"


def _form(form_id: str, user_id=None, groups=None) -> Form:
    section = Section(section_id=1, fields=[TextField(label="l", required=False, key="k", order=1)])
    return Form(
        id=form_id, form_title="Tapa-buraco", created_by=MANAGER_ID, user_id=user_id, system=SYSTEM,
        street="Rua 1", city="Uberlândia", latitude=-18.9, longitude=-48.2, priority=Priority.MEDIUM,
        status=FormStatus.PENDING, created_at=1, updated_at=1, sections=[section],
        justification=Justification(options=[JustificationOption(option="o", required_image=False, required_text=False)]),
        groups=groups,
    )


def _requester(user_id: str) -> UserGatewayDTO:
    return UserGatewayDTO(user_id=user_id, name="Pessoa", email="p@example.com", systems=[SYSTEM])


class GroupsScenario:
    def __init__(self):
        self.form_repo = FormRepositoryMock()
        self.form_repo.forms = [
            _form(FORM_GROUP_A, groups=[GROUP_A]),
            _form(FORM_USER_2, user_id=USERS[2]),
            _form(FORM_EVERYONE),
        ]
        self.profile_repo = ProfileRepositoryMock()
        self.role_repo = SystemRoleRepositoryMock()
        self.role_repo.put_role(SystemRole(system=SYSTEM, role_id="r-executor", name="Executor", actions=[],
                                           created_at=1, updated_at=1))
        self.role_repo.put_role(SystemRole(system=SYSTEM, role_id="r-gestor", name="Gestor",
                                           actions=[Action.FORMS_VIEW_ALL, Action.FORMS_ASSIGN],
                                           created_at=1, updated_at=1))
        for n, user_id in USERS.items():
            self._person(user_id, "r-executor", [GROUP_A] if n <= 5 else [GROUP_B])
        self._person(MANAGER_ID, "r-gestor", [])
        self.access_control = AccessControl(self.profile_repo, self.role_repo)

    def _person(self, user_id: str, role_id: str, groups):
        self.profile_repo.create(Profile(user_id=user_id, name=user_id[-2:], email=f"{user_id[-4:]}@example.com",
                                         active=True, created_at=1, updated_at=1))
        self.profile_repo.put_membership(SystemMembership(user_id=user_id, system=SYSTEM, role_id=role_id,
                                                          created_at=1, updated_at=1, groups=groups))

    def visible_to(self, user_id: str) -> set:
        """O que a pessoa vê na lista: as OS dela (`mine`) e as do pool."""
        usecase = GetAllFormsUsecase(self.form_repo, self.access_control)
        mine, _ = usecase(requester=_requester(user_id), limit=None, scope="mine")
        pool, _ = usecase(requester=_requester(user_id), limit=None, system=[SYSTEM], scope="pool")
        return {form.id for form in [*mine, *pool]}


class TestGroupsEvidence:
    def setup_method(self):
        self.scenario = GroupsScenario()

    @pytest.mark.parametrize("n", range(1, 11))
    def test_each_user_sees_exactly_what_the_plan_says(self, n):
        expected = {FORM_EVERYONE}
        if n <= 5:
            expected.add(FORM_GROUP_A)
        if n == 2:
            expected.add(FORM_USER_2)

        assert self.scenario.visible_to(USERS[n]) == expected

    def test_group_a_form_reaches_users_1_to_5(self):
        who = {n for n, user_id in USERS.items() if FORM_GROUP_A in self.scenario.visible_to(user_id)}
        assert who == {1, 2, 3, 4, 5}

    def test_directed_form_reaches_only_user_2(self):
        who = {n for n, user_id in USERS.items() if FORM_USER_2 in self.scenario.visible_to(user_id)}
        assert who == {2}

    def test_form_without_user_nor_groups_reaches_all_ten(self):
        who = {n for n, user_id in USERS.items() if FORM_EVERYONE in self.scenario.visible_to(user_id)}
        assert who == set(range(1, 11))

    def test_person_without_membership_sees_only_ungrouped_open_forms(self):
        outsider = "00000000-0000-4000-8000-000000000077"
        assert self.scenario.visible_to(outsider) == {FORM_EVERYONE}


class TestGroupsOnGetForm:
    def setup_method(self):
        self.scenario = GroupsScenario()
        self.usecase = GetFormUsecase(self.scenario.form_repo, self.scenario.access_control)

    def test_group_member_opens_the_form(self):
        assert self.usecase(USERS[3], FORM_GROUP_A).id == FORM_GROUP_A

    def test_other_group_is_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(USERS[7], FORM_GROUP_A)

    def test_view_all_opens_any_open_form(self):
        assert self.usecase(MANAGER_ID, FORM_GROUP_A).id == FORM_GROUP_A

    def test_ungrouped_open_form_stays_open_to_everyone(self):
        assert self.usecase(USERS[9], FORM_EVERYONE).id == FORM_EVERYONE


class TestGroupsOnClaim:
    def setup_method(self):
        self.scenario = GroupsScenario()
        self.usecase = ClaimFormUsecase(self.scenario.form_repo, FormEventRepositoryMock(), self.scenario.access_control)

    def test_group_member_claims(self):
        form = self.usecase(requester_user_id=USERS[1], requester_systems=[SYSTEM], form_id=FORM_GROUP_A)
        assert form.user_id == USERS[1]

    def test_other_group_cannot_claim(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(requester_user_id=USERS[6], requester_systems=[SYSTEM], form_id=FORM_GROUP_A)
        assert self.scenario.form_repo.get_form_by_id(user_id=USERS[6], form_id=FORM_GROUP_A).user_id is None

    def test_view_all_does_not_claim_outside_its_groups(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(requester_user_id=MANAGER_ID, requester_systems=[SYSTEM], form_id=FORM_GROUP_A)

    def test_claimed_form_leaves_the_pool_of_the_group(self):
        self.usecase(requester_user_id=USERS[1], requester_systems=[SYSTEM], form_id=FORM_GROUP_A)

        assert FORM_GROUP_A not in self.scenario.visible_to(USERS[3])
        assert FORM_GROUP_A in self.scenario.visible_to(USERS[1])
