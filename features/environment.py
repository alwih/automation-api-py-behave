import logging

from behave import fixture, use_fixture

from api import auth
from api.client import ApiClient, new_session
from api.redaction import redact, register_secret
from api.report import attach_exchange
from config.settings import load_settings

log = logging.getLogger("api")
BODY_LOG_LIMIT = 500  # characters of the response body to show for a failed step


def before_all(context):
    # Defining before_all replaces behave's default one, which only sets up logging
    context.config.setup_logging()
    # Read once and fail fast on bad config, before any request is sent
    context.settings = load_settings(context.config.userdata)
    # Kept out of failure output; /auth/me echoes the password back
    register_secret(context.settings.dummyjson_password)


@fixture
def dummyjson_login(context):
    # Logs in once for everything under the tag, which keeps clear of DummyJSON's rate limit
    session = new_session()
    try:
        client = ApiClient(session, context.settings.dummyjson_base_url, context.settings.request_timeout)
        response = auth.login(client, *auth.credentials(context.settings))
        assert response.status_code == 200, f"@authenticated login failed: {response.status_code} {response.text[:200]}"
        context.login = response.json()
        yield context.login
    finally:
        session.close()


def before_tag(context, tag):
    if tag == "authenticated":
        use_fixture(dummyjson_login, context)


def before_scenario(context, scenario):
    # Fresh session per scenario: shared connection pool, no state leaking between scenarios
    context.session = new_session()
    context.request_headers = {}  # extra headers for this scenario's requests, e.g. Authorization
    context.saved = {}  # values saved by steps, used as "{name}" in later steps
    # One client per service, all sharing this scenario's session
    context.clients = {
        service: ApiClient(context.session, base_url, context.settings.request_timeout)
        for service, base_url in context.settings.base_urls.items()
    }


def after_step(context, step):
    response = getattr(context, "response", None)
    if step.status.has_failed() and response is not None:
        body = redact(response.text)
        if len(body) > BODY_LOG_LIMIT:
            body = f"{body[:BODY_LOG_LIMIT]}... ({len(body)} chars total)"
        log.error("%s %s -> %s\n%s", response.request.method, response.request.url, response.status_code, body)
        # Untruncated request and response for the Allure report (ignored without -f allure)
        attach_exchange(response)


def after_scenario(context, scenario):
    context.session.close()
