import json

import parse
from behave import given, when, then, step, register_type
from api import assertions

@parse.with_pattern(r"GET|POST|PUT|PATCH|DELETE")
def parse_http_method(text):
    # parse matches custom types case-insensitively; keep the method canonical
    return text.upper()

@parse.with_pattern(r'the response|the "[^"]+" list')
def parse_item_list(text):
    # "the response" is a body that is itself a list; 'the "products" list' is a field holding one
    return "" if text.lower() == "the response" else text[len('the "'):-len('" list')]

@parse.with_pattern(r"ascending|descending")
def parse_sort_direction(text):
    return text.lower()

register_type(HttpMethod=parse_http_method, ItemList=parse_item_list, SortDirection=parse_sort_direction)

@given('the {service} API is available')
def use_service(context, service):
    assert service.lower() in context.clients, \
        f"Unknown service '{service}', expected one of {sorted(context.clients)}"
    context.client = context.clients[service.lower()]

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

def items_in(context, path):
    body = context.response.json()
    return assertions.field(body, path) if path else body

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

@then('{items:ItemList} should have {count:d} items')
def check_items_count(context, items, count):
    assertions.assert_list_length(items_in(context, items), count)

@then('{items:ItemList} should be empty')
def check_items_empty(context, items):
    assertions.assert_body_equals(items_in(context, items), [])

@then('every item in {items:ItemList} should have the fields "{fields}"')
def check_every_item_has_fields(context, items, fields):
    assertions.assert_every_item_has_fields(items_in(context, items), split_list(fields))

@then('every item in {items:ItemList} should have exactly the fields "{fields}"')
def check_every_item_has_exact_fields(context, items, fields):
    assertions.assert_every_item_has_exact_fields(items_in(context, items), split_list(fields))

@then('every item in {items:ItemList} should have "{field}" equal to {value:d}')
def check_every_item_field_int_value(context, items, field, value):
    assertions.assert_every_item_field_equals(items_in(context, items), field, value)

@then('every item in {items:ItemList} should have "{field}" equal to "{value}"')
def check_every_item_field_value(context, items, field, value):
    assertions.assert_every_item_field_equals(items_in(context, items), field, value)

@then('every item in {items:ItemList} should have "{field}" containing "{text}"')
def check_every_item_field_contains(context, items, field, text):
    assertions.assert_every_item_field_contains(items_in(context, items), field, text)

@then('every item in {items:ItemList} should contain "{text}" in any of "{fields}", ignoring case')
def check_every_item_mentions(context, items, text, fields):
    assertions.assert_every_item_mentions(items_in(context, items), split_list(fields), text)

@then('the "{field}" values in {items:ItemList} should be {values}')
def check_item_values_in_order(context, field, items, values):
    expected = [int(value) for value in split_list(values)]
    assertions.assert_item_values(items_in(context, items), field, expected)

@then('{items:ItemList} should be sorted by "{field}" in {direction:SortDirection} order')
def check_items_sorted(context, items, field, direction):
    assertions.assert_sorted(items_in(context, items), field, descending=direction == "descending")

@then('the response body should equal the remembered body')
def check_body_equals_remembered(context):
    assertions.assert_body_equals(context.response.json(), context.remembered_body)

@then('the response fields "{fields}" should match the remembered body')
def check_fields_match_remembered(context, fields):
    assertions.assert_fields_match(context.response.json(), context.remembered_body, split_list(fields))

@then('the response should echo the request body')
def check_echoes_request_body(context):
    assertions.assert_echoes(context.response.json(), context.request_body)
