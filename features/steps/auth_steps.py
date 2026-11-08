from behave import given, then, when

from api import assertions, auth, tokens
from api.step_data import body_from_table


def send_login(context, **overrides):
    username, password = auth.credentials(context.settings)
    # Saved so scenarios can check "{username}" without repeating the configured value
    context.saved["username"] = username
    fields = {"username": username, "password": password, **overrides}
    context.response = None
    context.response = auth.login(context.client, **fields)

@given('I am logged in')
def use_tagged_login(context):
    login = getattr(context, "login", None)
    assert login, "No login available: tag the feature or scenario with @authenticated"
    context.saved.update(access_token=login["accessToken"], refresh_token=login["refreshToken"],
                         user_id=login["id"])
    context.request_headers["Authorization"] = f"Bearer {login['accessToken']}"

@when('I log in as the configured user')
def log_in(context):
    send_login(context)

@when('I log in as the configured user with:')
def log_in_with(context):
    send_login(context, **body_from_table(context.table, context.saved))

@when('I log in as the configured user with the username in upper case')
def log_in_upper_case(context):
    username, _ = auth.credentials(context.settings)
    send_login(context, username=username.upper())

@when('I use the access token from the response')
def use_access_token_from_response(context):
    token = assertions.field(context.response.json(), "accessToken")
    context.request_headers["Authorization"] = f"Bearer {token}"

@given('I save a copy of "{name}" with a tampered signature as "{new_name}"')
def save_tampered_token(context, name, new_name):
    assert name in context.saved, f"Nothing saved as '{name}' yet; saved: {sorted(context.saved)}"
    context.saved[new_name] = tokens.tamper_signature(context.saved[name])

@then('the response field "{field}" should be a JWT')
def check_field_is_jwt(context, field):
    assertions.assert_field_is_jwt(context.response.json(), field)

@then('the "{field}" JWT should expire {minutes:d} minutes after it was issued')
def check_jwt_lifetime(context, field, minutes):
    token = assertions.field(context.response.json(), field)
    assertions.assert_jwt_lifetime(token, minutes * 60)
