import pytest

from src.shared.helpers.functions.pagination_token import (
    decode_pagination_token,
    encode_pagination_token,
    try_decode_pagination_token,
)


def test_pagination_token_roundtrip():
    token = encode_pagination_token({"PK": "form#1", "SK": "METADATA"})

    assert decode_pagination_token(token) == {"PK": "form#1", "SK": "METADATA"}


def test_decode_pagination_token_rejects_oversized_token():
    oversized = "a" * 10_241

    with pytest.raises(ValueError):
        decode_pagination_token(oversized)


def test_decode_pagination_token_rejects_too_many_keys():
    token = encode_pagination_token({str(index): index for index in range(21)})

    with pytest.raises(ValueError):
        decode_pagination_token(token)


def test_try_decode_pagination_token_returns_none_for_invalid_token():
    assert try_decode_pagination_token("not-base64") is None
