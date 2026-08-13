import json
import yaml
from jsonschema import validate, ValidationError


def validate_manifest(manifest_path: str, schema_path: str):
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    try:
        validate(instance=manifest, schema=schema)

        return {
            "valid": True,
            "errors": []
        }

    except ValidationError as e:
        return {
            "valid": False,
            "errors": [e.message]
        }