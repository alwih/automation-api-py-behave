import logging

import requests

log = logging.getLogger("api")
BODY_LOG_LIMIT = 500  # characters of the response body to show for a failed step


def before_scenario(context, scenario):
    # Fresh session per scenario: shared connection pool, no state leaking between scenarios
    context.session = requests.Session()
    context.session.headers.update({"Accept": "application/json"})


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
