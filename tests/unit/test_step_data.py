import pytest

from api.redaction import redact, register_secret
from api.step_data import body_from_table, resolve


def rows(*pairs):
    return [{"field": field, "value": value} for field, value in pairs]


def test_resolve_fills_in_saved_values():
    assert resolve("/products/{next_id}?q={term}", {"next_id": 195, "term": "phone"}) == "/products/195?q=phone"


def test_resolve_leaves_text_without_placeholders_alone():
    assert resolve('{"a": 1} and plain text', {}) == '{"a": 1} and plain text'


def test_resolve_fails_clearly_for_an_unknown_name():
    with pytest.raises(AssertionError, match=r"Nothing saved as 'nope' yet; saved: \['next_id'\]"):
        resolve("/products/{nope}", {"next_id": 195})


def test_body_from_table_reads_json_literals_and_keeps_other_text_as_strings():
    body = body_from_table(rows(("userId", "1"), ("price", "12.49"), ("flag", "true"),
                                ("quoted", '"1"'), ("title", "Café ☕ 日本語")))
    assert body == {"userId": 1, "price": 12.49, "flag": True, "quoted": "1", "title": "Café ☕ 日本語"}


def test_body_from_table_fills_placeholders_before_parsing():
    body = body_from_table(rows(("refreshToken", "{token}"), ("expiresInMins", "{minutes}")),
                           {"token": "a.b.c", "minutes": 30})
    assert body == {"refreshToken": "a.b.c", "expiresInMins": 30}


def test_body_from_a_header_only_table_is_empty():
    assert body_from_table([]) == {}


def test_redact_hides_every_registered_secret_and_ignores_empty_ones():
    register_secret("hunter2")
    register_secret("")      # an empty secret would otherwise put *** between every character
    register_secret(None)
    assert redact("password=hunter2, again hunter2") == "password=***, again ***"
