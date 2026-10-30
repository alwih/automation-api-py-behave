import json

import parse
from behave import given, when, then, step, register_type
from api.client import ApiClient
from test_data import BASE_URL, REQUEST_TIMEOUT

@parse.with_pattern(r"GET|POST|PUT|PATCH|DELETE")
def parse_http_method(text):
    # parse matches custom types case-insensitively; keep the method canonical
    return text.upper()

register_type(HttpMethod=parse_http_method)

@given('the API is ready')
def create_client(context):
    context.client = ApiClient(context.session, BASE_URL, REQUEST_TIMEOUT)

def body_from_table(table):
    # Values are JSON literals when they parse (1 -> int, true -> bool), otherwise strings.
    # Quote a value ("1") to send it as a string.
    body = {}
    for row in table:
        try:
            body[row["field"]] = json.loads(row["value"])
        except ValueError:
            body[row["field"]] = row["value"]
    return body

@given('I send a {method:HttpMethod} request to "{endpoint}"')
@when('I send a {method:HttpMethod} request to "{endpoint}"')
def send_request(context, method, endpoint):
    context.response = context.client.request(method, endpoint)

@given('I send a {method:HttpMethod} request to "{endpoint}" with:')
@when('I send a {method:HttpMethod} request to "{endpoint}" with:')
def send_request_with_table(context, method, endpoint):
    context.request_body = body_from_table(context.table)
    context.response = context.client.request(method, endpoint, json_body=context.request_body)

@step('I remember the response body')
def remember_response_body(context):
    context.remembered_body = context.response.json()

@then('the response status code should be {status_code:d}')
def check_status_code(context, status_code):
    assert context.response.status_code == status_code, \
        f"Expected {status_code} but got {context.response.status_code}"

@then('the response should contain "{field}"')
def check_field_exists(context, field):
    response_json = context.response.json()
    assert field in response_json, \
        f"Field '{field}' not found in response: {response_json}"

@then('the response field "{field}" should be "{value}"')
def check_field_value(context, field, value):
    response_json = context.response.json()
    assert response_json[field] == value, \
        f"Expected '{value}' but got '{response_json[field]}'"

@then('the response field "{field}" should be {value:d}')
def check_field_int_value(context, field, value):
    response_json = context.response.json()
    assert response_json[field] == value, \
        f"Expected {field} == {value} but got {response_json[field]!r}"

@then('the response field "{field}" should be an integer')
def check_field_is_integer(context, field):
    value = context.response.json()[field]
    # bool is a subclass of int, so rule it out explicitly
    assert isinstance(value, int) and not isinstance(value, bool), \
        f"Expected '{field}' to be an integer but got {value!r}"

@then('the response field "{field}" should be a non-empty string')
def check_field_is_non_empty_string(context, field):
    value = context.response.json()[field]
    assert isinstance(value, str) and value.strip(), \
        f"Expected '{field}' to be a non-empty string but got {value!r}"

@then('the response header "{name}" should be "{value}"')
def check_header_value(context, name, value):
    actual = context.response.headers.get(name)
    assert actual == value, \
        f"Expected header '{name}' to be '{value}' but got {actual!r}"

@then('the response header "{name}" should contain "{text}"')
def check_header_contains(context, name, text):
    actual = context.response.headers.get(name)
    assert actual is not None and text in actual, \
        f"Expected header '{name}' to contain '{text}' but got {actual!r}"

@then('the response body should be an empty object')
def check_body_empty_object(context):
    response_json = context.response.json()
    assert response_json == {}, f"Expected an empty object but got: {response_json}"

@then('the response body should be an empty list')
def check_body_empty_list(context):
    response_json = context.response.json()
    assert response_json == [], f"Expected an empty list but got: {response_json}"

@then('the response body should be a list of {count:d} items')
def check_list_length(context, count):
    response_json = context.response.json()
    assert isinstance(response_json, list), f"Expected a list but got: {response_json}"
    assert len(response_json) == count, \
        f"Expected {count} items but got {len(response_json)}"

def response_items(context):
    items = context.response.json()
    # "every item" checks must not pass silently on an empty list
    assert isinstance(items, list) and items, f"Expected a non-empty list but got: {items}"
    return items

@then('every item in the response should have the fields "{fields}"')
def check_every_item_has_fields(context, fields):
    expected = [name.strip() for name in fields.split(",")]
    for item in response_items(context):
        missing = [name for name in expected if name not in item]
        assert not missing, f"Item is missing {missing}: {item}"

@then('every item in the response should have "{field}" equal to {value:d}')
def check_every_item_field_value(context, field, value):
    for item in response_items(context):
        assert item[field] == value, f"Expected {field} == {value} but got: {item}"

@then('every item in the response should have "{field}" containing "{text}"')
def check_every_item_field_contains(context, field, text):
    for item in response_items(context):
        assert text in item[field], f"Expected {field} to contain '{text}' but got: {item}"

@then('the response items should have "{field}" values {values}')
def check_item_values_in_order(context, field, values):
    expected = [int(value) for value in values.split(",")]
    actual = [item[field] for item in response_items(context)]
    assert actual == expected, f"Expected {field} values {expected} but got {actual}"

@then('the response body should equal the remembered body')
def check_body_equals_remembered(context):
    response_json = context.response.json()
    assert response_json == context.remembered_body, \
        f"Expected {context.remembered_body} but got: {response_json}"

@then('the response fields "{fields}" should match the remembered body')
def check_fields_match_remembered(context, fields):
    response_json = context.response.json()
    for name in (field.strip() for field in fields.split(",")):
        assert name in response_json and name in context.remembered_body, \
            f"'{name}' missing from response {response_json} or remembered body {context.remembered_body}"
        assert response_json[name] == context.remembered_body[name], \
            f"Expected {name} == {context.remembered_body[name]!r} but got {response_json[name]!r}"

@then('the response should echo the request body')
def check_echoes_request_body(context):
    response_json = context.response.json()
    for field, value in context.request_body.items():
        assert field in response_json and response_json[field] == value, \
            f"Expected {field} == {value!r} but got: {response_json}"

@then('the response should not contain "{field}"')
def check_field_absent(context, field):
    response_json = context.response.json()
    assert field not in response_json, \
        f"Field '{field}' should not be in response: {response_json}"

@then('the response field "{field}" should be greater than {value:d}')
def check_field_greater_than(context, field, value):
    actual = context.response.json()[field]
    assert actual > value, f"Expected {field} > {value} but got {actual!r}"
