from __future__ import annotations

from typing import Optional
from pathlib import Path
import json

from .models import GateResult, GateDecision, GateViolation
from .loaders import load_structured_output_policy
from .evaluators import evaluate_structured_output

try:
    import jsonschema  # type: ignore
except Exception:
    jsonschema = None


class RouteGuardEngine:
    """
    Main orchestration engine for RouteGuard.

    Flow:
      (optional) JSON Schema validation  -> fail fast if invalid
      Structured output gate evaluation  -> ALLOW / DENY (+ details)
    """

    def __init__(self, policy_path: str):
        self.policy = load_structured_output_policy(policy_path)

        # Repo layout: routeguard/routeguard/engine.py -> parent is routeguard/routeguard
        # parent.parent is repo root "routeguard", where "spec/" lives.
        self._spec_dir = Path(__file__).resolve().parent.parent / "spec"

    def _load_schema(self, schema_name: str) -> dict:
        schema_path = self._spec_dir / schema_name
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")
        return json.loads(schema_path.read_text(encoding="utf-8"))

    def _schema_preflight(self, model_output: str) -> Optional[GateResult]:
        """
        If the policy specifies a schema, validate the model_output (as JSON) against it.
        Return a DENY GateResult on failure; otherwise None to continue.
        """
        schema_name = getattr(self.policy, "schema", None) or getattr(self.policy, "schema_file", None)
        if not schema_name:
            return None  # schema validation is optional

        if jsonschema is None:
            return GateResult(
                decision=GateDecision.DENY,
                violation=GateViolation(
                    reason="Schema validation requested but dependency missing.",
                    detail="Install 'jsonschema' (e.g. add it to pyproject.toml) to enable spec validation.",
                ),
            )

        # Parse JSON
        try:
            instance = json.loads(model_output)
        except Exception as e:
            return GateResult(
                decision=GateDecision.DENY,
                violation=GateViolation(
                    reason="Output is not valid JSON (required by schema validation).",
                    detail=str(e),
                ),
            )

        # Load + validate schema
        try:
            schema = self._load_schema(schema_name)
            jsonschema.validate(instance=instance, schema=schema)
        except FileNotFoundError as e:
            return GateResult(
                decision=GateDecision.DENY,
                violation=GateViolation(
                    reason="Schema file missing.",
                    detail=str(e),
                ),
            )
        except Exception as e:
            # jsonschema.ValidationError is the common case here, but keep it generic & safe.
            return GateResult(
                decision=GateDecision.DENY,
                violation=GateViolation(
                    reason="Schema validation failed.",
                    detail=str(e),
                ),
            )

        return None

    def evaluate_output(self, model_output: str, tool_name: Optional[str] = None) -> GateResult:
        """
        Apply the loaded policy to a model output string.
        """
        preflight = self._schema_preflight(model_output)
        if preflight is not None:
            return preflight

        return evaluate_structured_output(self.policy, model_output, tool_name=tool_name)
