"""Turn Gherkin step input (placeholders, data tables) into request data."""

import json
import re


def resolve(text, saved):
    # "{name}" is replaced by a value saved earlier in the scenario
    def saved_value(match):
        name = match.group(1)
        assert name in saved, f"Nothing saved as '{name}' yet; saved: {sorted(saved)}"
        return str(saved[name])

    return re.sub(r"\{(\w+)\}", saved_value, text)


def body_from_table(table, saved=None):
    # Values are JSON literals when they parse (1 -> int, true -> bool), otherwise strings.
    # Quote a value ("1") to send it as a string. "{name}" placeholders are filled in first.
    body = {}
    for row in table:
        value = resolve(row["value"], saved) if saved is not None else row["value"]
        try:
            body[row["field"]] = json.loads(value)
        except ValueError:
            body[row["field"]] = value
    return body
