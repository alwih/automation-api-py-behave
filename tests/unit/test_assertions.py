import pytest

from api import assertions
from api.redaction import register_secret

USER = {
    "id": 1,
    "address": {"geo": {"lat": "-37.3159"}},
    "tags": ["a", "b"],
    "products": [{"id": 7}],
    "note": None,
}


@pytest.mark.parametrize("path, expected", [
    ("id", 1),
    ("address.geo.lat", "-37.3159"),
    ("products.0.id", 7),
    ("tags.1", "b"),
    ("note", None),
])
def test_get_path_walks_objects_and_lists(path, expected):
    assert assertions.get_path(USER, path) == expected
    assert assertions.has_path(USER, path)


@pytest.mark.parametrize("path", [
    "missing",
    "address.geo.alt",
    "products.1.id",       # index past the end
    "products.-1.id",      # negative indexes are not supported
    "tags.first",          # lists only take numeric parts
    "address.geo.lat.x",   # can't walk into a string
])
def test_get_path_raises_key_error_for_missing_paths(path):
    with pytest.raises(KeyError):
        assertions.get_path(USER, path)
    assert not assertions.has_path(USER, path)


def test_field_reports_a_missing_path_as_a_failed_check():
    with pytest.raises(AssertionError, match=r"'address\.zip' not found: no 'zip'"):
        assertions.field(USER, "address.zip")


@pytest.mark.parametrize("values, descending", [
    ([1, 2, 2, 3], False),
    ([3, 2, 2, 1], True),
    ([5], False),
])
def test_assert_sorted_accepts_ordered_values_with_ties(values, descending):
    assertions.assert_sorted([{"price": value} for value in values], "price", descending=descending)


@pytest.mark.parametrize("values, descending, message", [
    ([1, 3, 2], False, "price not ascending at items 1 and 2: 3 then 2"),
    ([1, 2], True, "price not descending at items 0 and 1: 1 then 2"),
])
def test_assert_sorted_names_the_first_pair_out_of_order(values, descending, message):
    with pytest.raises(AssertionError, match=message):
        assertions.assert_sorted([{"price": value} for value in values], "price", descending=descending)


def test_every_item_checks_refuse_an_empty_list():
    with pytest.raises(AssertionError, match="Expected a non-empty list"):
        assertions.assert_sorted([], "price")
    with pytest.raises(AssertionError, match="Expected a non-empty list"):
        assertions.assert_every_item_field_equals([], "id", 1)


def test_every_item_mentions_passes_when_any_field_matches_ignoring_case():
    items = [{"title": "iPhone 15", "description": ""}, {"title": "Case", "description": "fits any PHONE"}]
    assertions.assert_every_item_mentions(items, ["title", "description"], "phone")
    with pytest.raises(AssertionError, match="Expected 'phone' in one of \\['title'\\]"):
        assertions.assert_every_item_mentions(items, ["title"], "phone")


@pytest.mark.parametrize("value, expected, passes", [
    (True, True, True),
    (False, False, True),
    (1, True, False),
    (0, False, False),
    ("true", True, False),
])
def test_boolean_check_does_not_accept_look_alikes(value, expected, passes):
    if passes:
        assertions.assert_field_is_boolean({"flag": value}, "flag", expected)
    else:
        with pytest.raises(AssertionError):
            assertions.assert_field_is_boolean({"flag": value}, "flag", expected)


@pytest.mark.parametrize("value, valid", [
    ("2026-11-02T01:24:20.168Z", True),
    ("2026-11-02T01:24:20+07:00", True),
    ("2026-11-02", False),               # a date, not a timestamp
    ("2026-13-02T00:00:00Z", False),     # month 13
    (1793582623, False),                 # epoch seconds
])
def test_iso_timestamp_check(value, valid):
    if valid:
        assertions.assert_field_is_iso_timestamp({"at": value}, "at")
    else:
        with pytest.raises(AssertionError, match="ISO 8601 timestamp"):
            assertions.assert_field_is_iso_timestamp({"at": value}, "at")


def test_failure_messages_hide_registered_secrets():
    register_secret("hunter2")
    with pytest.raises(AssertionError) as failure:
        assertions.assert_lacks_field({"password": "hunter2"}, "password")
    assert "hunter2" not in str(failure.value)
    assert "***" in str(failure.value)
