"""Validate response bodies against JSON Schemas in schemas/<service>/<name>.json.

Schemas are Draft 2020-12 and formats are checked ("date-time", "email",
"uri", ...). A schema can point at a sibling file with {"$ref": "product.json"}.
"""
import functools
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from api.redaction import redact

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
ERRORS_SHOWN = 5
MESSAGE_LIMIT = 200  # characters per error; a message can quote a whole response


def schema_path(service, name):
    return SCHEMA_DIR / service / f"{name}.json"


@functools.cache
def read_schema(path):
    if not path.is_file():
        raise FileNotFoundError(f"No schema file at {path}")
    schema = json.loads(path.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)  # a broken schema fails here, not mid-validation
    except SchemaError as error:
        raise ValueError(f"{path} is not a valid JSON Schema: {error.message}") from None
    # The file's URI becomes its base, so relative "$ref"s resolve to sibling files
    return {"$id": path.as_uri(), **schema}


def load_schema(service, name):
    return read_schema(schema_path(service, name))


def _retrieve(uri):
    path = Path(url2pathname(urlparse(uri).path))
    return Resource.from_contents(read_schema(path), default_specification=DRAFT202012)


REGISTRY = Registry(retrieve=_retrieve)


def _check(instance, schema, label):
    validator = Draft202012Validator(schema, registry=REGISTRY,
                                     format_checker=Draft202012Validator.FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(instance), key=lambda error: error.json_path)
    if errors:
        lines = [f"  {error.json_path}: {error.message[:MESSAGE_LIMIT]}" for error in errors[:ERRORS_SHOWN]]
        if len(errors) > ERRORS_SHOWN:
            lines.append(f"  ... and {len(errors) - ERRORS_SHOWN} more")
        count = f"{len(errors)} error{'s' if len(errors) != 1 else ''}"
        raise AssertionError(redact(f"Response does not match {label} ({count}):\n" + "\n".join(lines)))


def validate(instance, service, name):
    _check(instance, load_schema(service, name), f"the {service} '{name}' schema")


def validate_each(items, service, name):
    # One array schema, so errors point at the item: $[3].id
    load_schema(service, name)
    wrapper = {"type": "array", "minItems": 1, "items": {"$ref": schema_path(service, name).as_uri()}}
    _check(items, wrapper, f"the {service} '{name}' schema for every item")
