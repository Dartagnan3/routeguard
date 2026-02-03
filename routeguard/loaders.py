import json
from pathlib import Path
from typing import Any, Dict, Union

from .models import GateMode, StructuredOutputGatePolicy


JsonLike = Union[Dict[str, Any], str, Path]


def _load_json(source: JsonLike) -> Dict[str, Any]:
    """
    Load JSON from:
      - dict (pass-through)
      - str (raw json string OR filepath)
      - Path (filepath)
    """
    if isinstance(source, dict):
        return source

    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
        return json.loads(text)

    if isinstance(source, str):
        s = source.strip()
        # Heuristic: if it looks like JSON, parse directly
        if s.startswith("{") or s.startswith("["):
            data = json.loads(s)
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object (dict) at top-level.")
            return data
        # Otherwise treat as a path
        p = Path(s)
        if not p.exists():
            raise FileNotFoundError(f"JSON path not found: {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    raise TypeError(f"Unsupported JSON source type: {type(source)}")


def load_structured_output_policy(source: JsonLike) -> StructuredOutputGatePolicy:
    """
    Loads a StructuredOutputGatePolicy from JSON that matches your example:
      {
        "policy_id": "...",
        "version": "...",
        "mode": "STRICT" | "LENIENT",
        "allow_codeblock": bool,
        "allow_substring_extraction": bool,
        "allow_repair": bool,
        "notes": str?,
        "timestamp": str?
      }
    """
    data = _load_json(source)

    required = [
        "policy_id",
        "version",
        "mode",
        "allow_codeblock",
        "allow_substring_extraction",
        "allow_repair",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    mode_raw = data["mode"]
    try:
        mode = GateMode(mode_raw)
    except Exception as e:
        raise ValueError(f"Invalid mode '{mode_raw}'. Must be STRICT or LENIENT.") from e

    # Hard type checks (so we fail loudly, early)
    if not isinstance(data["policy_id"], str):
        raise TypeError("policy_id must be a string")
    if not isinstance(data["version"], str):
        raise TypeError("version must be a string")
    for b in ["allow_codeblock", "allow_substring_extraction", "allow_repair"]:
        if not isinstance(data[b], bool):
            raise TypeError(f"{b} must be a boolean")

    notes = data.get("notes")
    if notes is not None and not isinstance(notes, str):
        raise TypeError("notes must be a string if present")

    timestamp = data.get("timestamp")
    if timestamp is not None and not isinstance(timestamp, str):
        raise TypeError("timestamp must be a string if present")

    return StructuredOutputGatePolicy(
        policy_id=data["policy_id"],
        version=data["version"],
        mode=mode,
        allow_codeblock=data["allow_codeblock"],
        allow_substring_extraction=data["allow_substring_extraction"],
        allow_repair=data["allow_repair"],
        notes=notes,
        timestamp=timestamp,
    )
