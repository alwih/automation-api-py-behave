import requests


def before_scenario(context, scenario):
    # Fresh session per scenario: shared connection pool, no state leaking between scenarios
    context.session = requests.Session()
    context.session.headers.update({"Accept": "application/json"})


def after_scenario(context, scenario):
    context.session.close()
