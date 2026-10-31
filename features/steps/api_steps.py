import json

import parse
from behave import given, when, then, step, register_type
from api import assertions
from api.client import ApiClient

@parse.with_pattern(r"GET|POST|PUT|PATCH|DELETE")
def parse_http_method(text):
    # parse matches custom types case-insensitively; keep the method canonical
    return text.upper()

register_type(HttpMethod=parse_http_method)

@given('the API is ready')
def create_client(context):
    settings = context.settings
    context.client = ApiClient(context.session, settings.jsonplaceholder_base_url, settings.request_timeout)

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
    context.response = None  # so a request that raises doesn't leave the previous response behind
    context.response = context.client.request(method, endpoint)

@given('I send a {method:HttpMethod} request to "{endpoint}" with:')
@when('I send a {method:HttpMethod} request to "{endpoint}" with:')
def send_request_with_table(context, method, endpoint):
    context.request_body = body_from_table(context.table)
    context.response = None
    context.response = context.client.request(method, endpoint, json_body=context.request_body)

@step('I remember the response body')
def remember_response_body(context):
    context.remembered_body = context.response.json()

def split_list(text):
    return [part.strip() for part in text.split(",")]

@then('the response status code should be {status_code:d}')
def check_status_code(context, status_code):
    assertions.assert_status(context.response, status_code)

@then('the response should contain "{field}"')
def check_field_exists(context, field):
    assertions.assert_has_field(context.response.json(), field)

@then('the response should not contain "{field}"')
def check_field_absent(context, field):
    assertions.assert_lacks_field(context.response.json(), field)

@then('the response field "{field}" should be "{value}"')
def check_field_value(context, field, value):
    assertions.assert_field_equals(context.response.json(), field, value)

@then('the response field "{field}" should be {value:d}')
def check_field_int_value(context, field, value):
    assertions.assert_field_equals(context.response.json(), field, value)

@then('the response field "{field}" should be an integer')
def check_field_is_integer(context, field):
    assertions.assert_field_is_integer(context.response.json(), field)

@then('the response field "{field}" should be a non-empty string')
def check_field_is_non_empty_string(context, field):
    assertions.assert_field_is_non_empty_string(context.response.json(), field)

@then('the response field "{field}" should be greater than {value:d}')
def check_field_greater_than(context, field, value):
    assertions.assert_field_greater_than(context.response.json(), field, value)

@then('the response header "{name}" should be "{value}"')
def check_header_value(context, name, value):
    assertions.assert_header_equals(context.response, name, value)

@then('the response header "{name}" should contain "{text}"')
def check_header_contains(context, name, text):
    assertions.assert_header_contains(context.response, name, text)

@then('the response body should be an empty object')
def check_body_empty_object(context):
    assertions.assert_body_equals(context.response.json(), {})

@then('the response body should be an empty list')
def check_body_empty_list(context):
    assertions.assert_body_equals(context.response.json(), [])

@then('the response body should be a list of {count:d} items')
def check_list_length(context, count):
    assertions.assert_list_length(context.response.json(), count)

@then('every item in the response should have the fields "{fields}"')
def check_every_item_has_fields(context, fields):
    assertions.assert_every_item_has_fields(context.response.json(), split_list(fields))

@then('every item in the response should have "{field}" equal to {value:d}')
def check_every_item_field_value(context, field, value):
    assertions.assert_every_item_field_equals(context.response.json(), field, value)

@then('every item in the response should have "{field}" containing "{text}"')
def check_every_item_field_contains(context, field, text):
    assertions.assert_every_item_field_contains(context.response.json(), field, text)

@then('the response items should have "{field}" values {values}')
def check_item_values_in_order(context, field, values):
    expected = [int(value) for value in split_list(values)]
    assertions.assert_item_values(context.response.json(), field, expected)

@then('the response body should equal the remembered body')
def check_body_equals_remembered(context):
    assertions.assert_body_equals(context.response.json(), context.remembered_body)

@then('the response fields "{fields}" should match the remembered body')
def check_fields_match_remembered(context, fields):
    assertions.assert_fields_match(context.response.json(), context.remembered_body, split_list(fields))

@then('the response should echo the request body')
def check_echoes_request_body(context):
    assertions.assert_echoes(context.response.json(), context.request_body)
