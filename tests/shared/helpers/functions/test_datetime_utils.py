from src.shared.helpers.functions.datetime_utils import now_timestamp_ms, utc_year


def test_now_timestamp_ms_returns_millisecond_timestamp():
    timestamp = now_timestamp_ms()

    assert isinstance(timestamp, int)
    assert timestamp > 1_000_000_000_000


def test_utc_year_returns_current_year():
    year = utc_year()

    assert isinstance(year, int)
    assert year >= 2024
