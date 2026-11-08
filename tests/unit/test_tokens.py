import base64
import json

import pytest

from api import assertions
from api.tokens import decode_jwt, tamper_signature


def segment(data):
    raw = data if isinstance(data, bytes) else json.dumps(data).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def make_jwt(payload, header=None, signature="c2lnbmF0dXJl"):
    return f"{segment(header or {'alg': 'HS256', 'typ': 'JWT'})}.{segment(payload)}.{signature}"


def test_decode_jwt_returns_header_and_payload():
    header, payload = decode_jwt(make_jwt({"id": 1, "iat": 100, "exp": 160}))
    assert header == {"alg": "HS256", "typ": "JWT"}
    assert payload == {"id": 1, "iat": 100, "exp": 160}


@pytest.mark.parametrize(
    "token, reason",
    [
        ("not.a.jwt", "not base64url JSON"),
        ("only.two", "expected 3 dot-separated segments, got 2"),
        (None, "expected 3 dot-separated segments, got 0"),
        (f"{segment({'alg': 'HS256'})}.{segment(b'not json')}.sig", "not base64url JSON"),
        (f"{segment({'alg': 'HS256'})}.{segment([1, 2])}.sig", "must be JSON objects"),
    ],
)
def test_decode_jwt_rejects_anything_that_is_not_a_jwt(token, reason):
    with pytest.raises(ValueError, match=reason):
        decode_jwt(token)


def test_tamper_signature_changes_only_the_signature():
    token = make_jwt({"id": 1})
    tampered = tamper_signature(token)
    assert tampered != token
    assert tampered.rsplit(".", 1)[0] == token.rsplit(".", 1)[0]


@pytest.mark.parametrize("signature, expected", [("xyz", "Ayz"), ("Abc", "Bbc")])
def test_tamper_signature_always_changes_the_first_character(signature, expected):
    assert tamper_signature(f"h.p.{signature}") == f"h.p.{expected}"


def test_jwt_lifetime_check_compares_exp_minus_iat():
    token = make_jwt({"iat": 1000, "exp": 1060})
    assertions.assert_jwt_lifetime(token, 60)
    with pytest.raises(AssertionError, match=r"last 1800s .* but it lasts 60s"):
        assertions.assert_jwt_lifetime(token, 1800)
