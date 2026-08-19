from src.shared.environments import Environments, Stage


def test_environments_parse_bool():
    assert Environments._parse_bool(True) is True
    assert Environments._parse_bool("true") is True
    assert Environments._parse_bool("1") is True
    assert Environments._parse_bool("on") is True
    assert Environments._parse_bool("false") is False
    assert Environments._parse_bool(None) is False


def test_environments_parse_csv():
    assert Environments._parse_csv("GAIA, SGC,GAIA,, ") == ("GAIA", "SGC")
    assert Environments._parse_csv(None) == ()


def test_environments_get_envs_caches_and_resets(monkeypatch):
    Environments._reset_instance()
    monkeypatch.setenv("STAGE", "TEST")

    first = Environments.get_envs()
    second = Environments.get_envs()

    assert first is second
    assert first.stage is Stage.TEST

    Environments._reset_instance()
    third = Environments.get_envs()

    assert third is not first

    Environments._reset_instance()
