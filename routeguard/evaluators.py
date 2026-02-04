from typing import List, Optional

from .models import StructuredOutputGatePolicy, GateMode, GateDecision


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


def _is_valid_json(text: str) -> bool:
    import json
    try:
        obj = json.loads(text)
        return isinstance(obj, dict)
    except Exception:
        return False


def _normalize_tool_name(tool_name: str) -> str:
    # keep it simple + stable: trim whitespace
    return tool_name.strip()


def _check_tool_permissions(
    policy: StructuredOutputGatePolicy,
    tool_name: Optional[str],
) -> Optional[GateDecision]:
    """
    Returns a GateDecision (DENY) if tool is not permitted, else None.
    Priority:
      1) forbidden_tools blocks always
      2) allowed_tools (if present) is an allowlist
    """
    if not tool_name:
        return None

    t = _normalize_tool_name(tool_name)

    # 1) Deny if explicitly forbidden
    if policy.forbidden_tools is not None and t in policy.forbidden_tools:
        return GateDecision.deny(reason="Tool permission not granted.")

    # 2) If an allowlist exists, deny anything not on it
    if policy.allowed_tools is not None and t not in policy.allowed_tools:
        return GateDecision.deny(reason="Tool permission not granted.")

    return None


def evaluate_structured_output(
    policy: StructuredOutputGatePolicy,
    model_output: str,
    tool_name: Optional[str] = None,
) -> GateDecision:
    """
    Apply a StructuredOutputGatePolicy to a model output string.
    Returns a GateDecision.

    tool_name (optional):
      If provided, enforces policy.allowed_tools / policy.forbidden_tools.
    """

    # 0) Tool permission gate (if tool_name provided)
    tool_gate = _check_tool_permissions(policy, tool_name)
    if tool_gate is not None:
        return tool_gate

    text = model_output.strip()

    # 1. Codeblock rule
    if not policy.allow_codeblock and _contains_codeblock(text):
        return GateDecision.deny(
            reason="Code blocks are not allowed under this policy."
        )

    # 2. STRICT mode: must be raw JSON only
    if policy.mode == GateMode.STRICT:
        if _looks_like_wrapped_json(text):
            return GateDecision.deny(
                reason="STRICT mode: output must be raw JSON only (no wrappers)."
            )
        if not _is_valid_json(text):
            return GateDecision.deny(
                reason="STRICT mode: output must be valid JSON object."
            )

    # 3. LENIENT mode: allow wrapper, but must contain extractable JSON
    if policy.mode == GateMode.LENIENT:
        import json
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

        if extracted is None:
            return GateDecision.deny(
                reason="LENIENT mode: could not extract valid JSON."
            )

    # 4. If we reached here, we passed
    return GateDecision.allow(
        notes="Structured output accepted under policy."
    )
