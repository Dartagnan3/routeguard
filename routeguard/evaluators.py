from typing import Optional
import json

from .models import (
    StructuredOutputGatePolicy,
    GateMode,
    GateDecision,
    GateResult,
    InvariantViolation,
)


def _contains_codeblock(text: str) -> bool:
    return "```" in text


def _looks_like_wrapped_json(text: str) -> bool:
    """
    Detects cases like:
      Sure! Here is the JSON:
      { ... }
    instead of raw JSON only.
    """
    stripped = text.strip()
    if not stripped.startswith("{"):
        return True
    if not stripped.endswith("}"):
        return True
    return False


def _is_valid_json_object(text: str) -> bool:
    try:
        obj = json.loads(text)
        return isinstance(obj, dict)
    except Exception:
        return False


def evaluate_structured_output(
    policy: StructuredOutputGatePolicy,
    model_output: str,
    tool_name: Optional[str] = None,
) -> GateResult:
    """
    Apply a StructuredOutputGatePolicy to a model output string.
    Returns a GateResult (decision + optional reason/violation).
    """

    text = model_output.strip()

    # 0) Tool permission gate (if tool_name is provided)
    # - If forbidden_tools is set, deny if tool_name is in it
    # - If allowed_tools is set, deny if tool_name is not in it
    if tool_name:
        if policy.forbidden_tools and tool_name in policy.forbidden_tools:
            return GateResult(
                decision=GateDecision.DENY,
                violation=InvariantViolation(
                    reason="Tool permission not granted.",
                    detail=f"Tool '{tool_name}' is forbidden by policy.",
                ),
            )
        if policy.allowed_tools and tool_name not in policy.allowed_tools:
            return GateResult(
                decision=GateDecision.DENY,
                violation=InvariantViolation(
                    reason="Tool permission not granted.",
                    detail=f"Tool '{tool_name}' is not in allowed_tools.",
                ),
            )

    # 1) Codeblock rule
    if not policy.allow_codeblock and _contains_codeblock(text):
        return GateResult(
            decision=GateDecision.DENY,
            violation=InvariantViolation(
                reason="Code blocks are not allowed under this policy."
            ),
        )

    # 2) STRICT mode: must be raw JSON only
    if policy.mode == GateMode.STRICT:
        if _looks_like_wrapped_json(text):
            return GateResult(
                decision=GateDecision.DENY,
                violation=InvariantViolation(
                    reason="STRICT mode: output must be raw JSON only (no wrappers)."
                ),
            )
        if not _is_valid_json_object(text):
            return GateResult(
                decision=GateDecision.DENY,
                violation=InvariantViolation(
                    reason="STRICT mode: output must be valid JSON object."
                ),
            )

    # 3) LENIENT mode: allow wrapper, but must contain extractable JSON
    if policy.mode == GateMode.LENIENT:
        extracted = None

        try:
            extracted = json.loads(text)
        except Exception:
            # Try substring extraction if allowed
            if policy.allow_substring_extraction:
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    candidate = text[start : end + 1]
                    try:
                        extracted = json.loads(candidate)
                    except Exception:
                        extracted = None

        if extracted is None or not isinstance(extracted, dict):
            return GateResult(
                decision=GateDecision.DENY,
                violation=InvariantViolation(
                    reason="LENIENT mode: could not extract valid JSON object."
                ),
            )

    # 4) Passed
    return GateResult(
        decision=GateDecision.ALLOW,
        violation=None,
        repaired_output=None,
    )
