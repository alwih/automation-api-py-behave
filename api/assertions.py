"""Response checks used by the step definitions.

Field paths are dotted: "address.geo.lat" walks nested objects, and a
numeric part indexes a list, so "products.0.id" is the first product's id.
"""
import functools
from datetime import datetime

from api.redaction import redact
from api.tokens import decode_jwt


def get_path(data, path):
    current = data
    for key in path.split("."):
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and key.isdigit() and int(key) < len(current):
            current = current[int(key)]
        else:
            raise KeyError(f"'{path}' not found: no '{key}' in {current!r}")
    return current


def has_path(data, path):
    try:
        get_path(data, path)
    except KeyError:
        return False
    return True


def field(data, path):
    # A missing field is a failed check, not a crash in the step
    try:
        return get_path(data, path)
    except KeyError as error:
        raise AssertionError(error.args[0]) from None


def assert_status(response, expected):
    assert response.status_code == expected, \
        f"Expected {expected} but got {response.status_code}"


def assert_header_equals(response, name, expected):
    actual = response.headers.get(name)
    assert actual == expected, \
        f"Expected header '{name}' to be '{expected}' but got {actual!r}"


def assert_header_contains(response, name, text):
    actual = response.headers.get(name)
    assert actual is not None and text in actual, \
        f"Expected header '{name}' to contain '{text}' but got {actual!r}"


def assert_has_field(body, path):
    assert has_path(body, path), f"Field '{path}' not found in response: {body}"


def assert_lacks_field(body, path):
    assert not has_path(body, path), f"Field '{path}' should not be in response: {body}"


def assert_field_equals(body, path, expected):
    actual = field(body, path)
    assert actual == expected, f"Expected {path} == {expected!r} but got {actual!r}"


def assert_field_is_integer(body, path):
    value = field(body, path)
    # bool is a subclass of int, so rule it out explicitly
    assert isinstance(value, int) and not isinstance(value, bool), \
        f"Expected '{path}' to be an integer but got {value!r}"


def assert_field_is_non_empty_string(body, path):
    value = field(body, path)
    assert isinstance(value, str) and value.strip(), \
        f"Expected '{path}' to be a non-empty string but got {value!r}"


def assert_field_greater_than(body, path, minimum):
    actual = field(body, path)
    assert actual > minimum, f"Expected {path} > {minimum} but got {actual!r}"


def assert_field_is_boolean(body, path, expected):
    actual = field(body, path)
    # Identity, so 1 and 0 don't pass as true and false
    assert actual is expected, f"Expected {path} to be {expected} but got {actual!r}"


def assert_field_is_iso_timestamp(body, path):
    value = field(body, path)
    try:
        # fromisoformat only accepts a trailing "Z" from Python 3.11 on
        valid = isinstance(value, str) and "T" in value and bool(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        valid = False
    assert valid, f"Expected '{path}' to be an ISO 8601 timestamp but got {value!r}"


def assert_field_is_jwt(body, path):
    value = field(body, path)
    try:
        decode_jwt(value)
    except ValueError as error:
        raise AssertionError(f"Expected '{path}' to be a JWT, but {error}: {value!r:.80}") from None


def assert_jwt_lifetime(token, seconds):
    _, payload = decode_jwt(token)
    lifetime = payload["exp"] - payload["iat"]
    assert lifetime == seconds, \
        f"Expected the token to last {seconds}s (exp - iat) but it lasts {lifetime}s"


def assert_fields_equal(body, path, other_path):
    actual, other = field(body, path), field(body, other_path)
    assert actual == other, f"Expected {path} ({actual!r}) to equal {other_path} ({other!r})"


def assert_body_equals(body, expected):
    assert body == expected, f"Expected {expected} but got: {body}"


def assert_list_length(body, count):
    assert isinstance(body, list), f"Expected a list but got: {body}"
    assert len(body) == count, f"Expected {count} items but got {len(body)}"


def non_empty_list(body):
    # "every item" checks must not pass silently on an empty list
    assert isinstance(body, list) and body, f"Expected a non-empty list but got: {body}"
    return body


def assert_every_item_has_fields(body, paths):
    for item in non_empty_list(body):
        missing = [path for path in paths if not has_path(item, path)]
        assert not missing, f"Item is missing {missing}: {item}"


def assert_every_item_field_equals(body, path, expected):
    for item in non_empty_list(body):
        assert field(item, path) == expected, f"Expected {path} == {expected!r} but got: {item}"


def assert_every_item_field_contains(body, path, text):
    for item in non_empty_list(body):
        assert text in field(item, path), f"Expected {path} to contain '{text}' but got: {item}"


def assert_every_item_has_exact_fields(body, names):
    for item in non_empty_list(body):
        assert set(item) == set(names), \
            f"Expected exactly {sorted(names)} but got {sorted(item)}: {item}"


def assert_every_item_mentions(body, paths, text):
    # Passes when at least one of the fields contains the text, ignoring case
    needle = text.lower()
    for item in non_empty_list(body):
        assert any(needle in str(field(item, path)).lower() for path in paths), \
            f"Expected '{text}' in one of {paths} but got: {item}"


def assert_sorted(body, path, descending=False):
    values = [field(item, path) for item in non_empty_list(body)]
    # Equal neighbours are fine; only a strictly out-of-order pair fails
    for index, (current, following) in enumerate(zip(values, values[1:])):
        in_order = current >= following if descending else current <= following
        assert in_order, (f"{path} not {'descending' if descending else 'ascending'} "
                          f"at items {index} and {index + 1}: {current!r} then {following!r}")


def assert_item_values(body, path, expected):
    actual = [field(item, path) for item in non_empty_list(body)]
    assert actual == expected, f"Expected {path} values {expected} but got {actual}"


def assert_fields_match(body, expected_body, paths):
    for path in paths:
        assert has_path(body, path) and has_path(expected_body, path), \
            f"'{path}' missing from response {body} or remembered body {expected_body}"
        expected = get_path(expected_body, path)
        actual = get_path(body, path)
        assert actual == expected, f"Expected {path} == {expected!r} but got {actual!r}"


def assert_echoes(body, sent):
    # Request bodies are flat (one key per table row), so compare top-level keys
    for key, value in sent.items():
        assert isinstance(body, dict) and key in body and body[key] == value, \
            f"Expected {key} == {value!r} but got: {body}"


def _hide_secrets(check):
    @functools.wraps(check)
    def wrapper(*args, **kwargs):
        try:
            return check(*args, **kwargs)
        except AssertionError as error:
            raise AssertionError(redact(str(error))) from None
    return wrapper


# Failure messages quote response bodies; make every check above hide registered secrets
for _name, _check in list(globals().items()):
    if callable(_check) and (_name.startswith("assert_") or _name in ("field", "non_empty_list")):
        globals()[_name] = _hide_secrets(_check)
