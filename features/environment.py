import logging

import requests

from api.client import ApiClient
from config.settings import load_settings

log = logging.getLogger("api")
BODY_LOG_LIMIT = 500  # characters of the response body to show for a failed step


def before_all(context):
    # Read once and fail fast on bad config, before any request is sent
    context.settings = load_settings(context.config.userdata)


def before_scenario(context, scenario):
    # Fresh session per scenario: shared connection pool, no state leaking between scenarios
    context.session = requests.Session()
    context.session.headers.update({"Accept": "application/json"})
    # One client per service, all sharing this scenario's session
    context.clients = {
        service: ApiClient(context.session, base_url, context.settings.request_timeout)
        for service, base_url in context.settings.base_urls.items()
    }


def after_step(context, step):
    response = getattr(context, "response", None)
    if step.status.has_failed() and response is not None:
        body = response.text
        if len(body) > BODY_LOG_LIMIT:
            body = f"{body[:BODY_LOG_LIMIT]}... ({len(body)} chars total)"
        log.error("%s %s -> %s\n%s", response.request.method, response.request.url,
                  response.status_code, body)


def after_scenario(context, scenario):
    context.session.close()
