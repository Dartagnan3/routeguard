import json
from jsonschema import validate, ValidationError
from pathlib import Path

def validate_against_schema(json_text: str, schema_path: Path) -> tuple[bool, str | None]:
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

    try:
        schema = json.loads(schema_path.read_text())
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Schema violation: {e.message}"
