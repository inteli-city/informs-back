from datetime import datetime, timezone


def now_timestamp_ms() -> int:
    """Returns the current UTC time as an integer millisecond timestamp."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def utc_year() -> int:
    """Returns the current UTC year (used for S3 path prefixes)."""
    return datetime.now(timezone.utc).year
