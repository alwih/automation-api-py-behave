import json

import pytest
from jsonschema import Draft202012Validator

from api import schema
from api.redaction import register_secret

ITEM = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["id", "when", "site"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "when": {"type": "string", "format": "date-time"},
        "site": {"type": "string", "format": "uri"},
    },
}
GOOD = {"id": 1, "when": "2026-11-02T01:24:20.168Z", "site": "https://example.org/a"}


@pytest.fixture
def schema_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(schema, "SCHEMA_DIR", tmp_path)
    schema.read_schema.cache_clear()
    yield tmp_path
    schema.read_schema.cache_clear()


def write(directory, name, content):
    path = directory / "svc" / f"{name}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(content if isinstance(content, str) else json.dumps(content))
    return path


def test_every_schema_in_the_repo_is_a_valid_json_schema():
    paths = sorted(schema.SCHEMA_DIR.glob("*/*.json"))
    assert paths, f"no schemas found in {schema.SCHEMA_DIR}"
    for path in paths:
        schema.read_schema(path)


def test_formats_used_by_the_schemas_are_enforced():
    # jsonschema silently skips a format whose helper library isn't installed
    assert {"date-time", "uri", "email"} <= set(Draft202012Validator.FORMAT_CHECKER.checkers)


def test_loading_a_missing_schema_names_the_expected_file(schema_dir):
    with pytest.raises(FileNotFoundError, match=r"svc/nope\.json"):
        schema.validate(GOOD, "svc", "nope")


def test_loading_a_file_that_is_not_json_fails(schema_dir):
    write(schema_dir, "broken", "{not json")
    with pytest.raises(json.JSONDecodeError):
        schema.validate(GOOD, "svc", "broken")


def test_loading_an_invalid_schema_names_the_file(schema_dir):
    write(schema_dir, "bad", {"type": "not-a-type"})
    with pytest.raises(ValueError, match=r"bad\.json is not a valid JSON Schema"):
        schema.validate(GOOD, "svc", "bad")


def test_valid_instance_passes(schema_dir):
    write(schema_dir, "item", ITEM)
    schema.validate(GOOD, "svc", "item")


def test_errors_list_each_path_including_format_failures(schema_dir):
    write(schema_dir, "item", ITEM)
    with pytest.raises(AssertionError) as failure:
        schema.validate({"id": "x", "when": "yesterday"}, "svc", "item")
    message = str(failure.value)
    assert "(3 errors)" in message
    assert "$: 'site' is a required property" in message
    assert "$.id: 'x' is not of type 'integer'" in message
    assert "$.when: 'yesterday' is not a 'date-time'" in message


def test_ref_to_a_sibling_file_is_resolved(schema_dir):
    write(schema_dir, "item", ITEM)
    page = {"type": "object", "properties": {"items": {"type": "array", "items": {"$ref": "item.json"}}}}
    write(schema_dir, "page", page)
    with pytest.raises(AssertionError, match=r"\$\.items\[1\]\.site: 'not a uri' is not a 'uri'"):
        schema.validate({"items": [GOOD, {**GOOD, "site": "not a uri"}]}, "svc", "page")


def test_validate_each_points_at_the_failing_item_and_rejects_empty_lists(schema_dir):
    write(schema_dir, "item", ITEM)
    with pytest.raises(AssertionError, match=r"\$\[2\]\.id: 0 is less than the minimum of 1"):
        schema.validate_each([GOOD, GOOD, {**GOOD, "id": 0}], "svc", "item")
    with pytest.raises(AssertionError, match=r"\[\] should be non-empty"):
        schema.validate_each([], "svc", "item")


def test_long_error_lists_are_capped(schema_dir):
    write(schema_dir, "item", ITEM)
    with pytest.raises(AssertionError) as failure:
        schema.validate_each([{}, {}, {}], "svc", "item")
    assert "(9 errors)" in str(failure.value)
    assert "... and 4 more" in str(failure.value)


def test_a_failed_not_rule_shows_its_description(schema_dir):
    login = {"type": "object", "not": {"description": "Never include the password", "required": ["password"]}}
    write(schema_dir, "login", login)
    with pytest.raises(AssertionError, match="breaks rule: Never include the password"):
        schema.validate({"password": "x"}, "svc", "login")


def test_error_messages_hide_registered_secrets(schema_dir):
    write(schema_dir, "item", ITEM)
    register_secret("hunter2")
    with pytest.raises(AssertionError) as failure:
        schema.validate({**GOOD, "id": "hunter2"}, "svc", "item")
    assert "hunter2" not in str(failure.value)
