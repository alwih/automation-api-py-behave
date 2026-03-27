import requests
from behave import given, when, then
from test_data import BASE_URL, POST_PAYLOAD, PUT_PAYLOAD, PATCH_PAYLOAD

@given('the API is ready')
def set_base_url(context):
    context.base_url = BASE_URL

@when('I send a GET request to "{endpoint}"')
def send_get_request(context, endpoint):
    url = context.base_url + endpoint
    context.response = requests.get(url)

@when('I send a POST request to "{endpoint}"')
def send_post_request(context, endpoint):
    url = context.base_url + endpoint
    context.response = requests.post(url, json=POST_PAYLOAD)

@when('I send a PUT request to "{endpoint}"')
def send_put_request(context, endpoint):
    url = context.base_url + endpoint
    context.response = requests.put(url, json=PUT_PAYLOAD)

@when('I send a PATCH request to "{endpoint}"')
def send_patch_request(context, endpoint):
    url = context.base_url + endpoint
    context.response = requests.patch(url, json=PATCH_PAYLOAD)

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
