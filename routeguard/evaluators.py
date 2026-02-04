from typing import Optional

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


def _tool_is_allowed(policy: StructuredOutputGatePolicy, tool_name: str) -> bool:
    """
    Tool permission logic:
      - if forbidden_tools contains tool_name => deny
      - if allowed_tools is set (non-empty) and tool_name not in it => deny
      - otherwise allow
    """
    if policy.forbidden_tools and tool_name in policy.forbidden_tools:
        return False
    if policy.allowed_tools is not None:
        # allowed_tools provided: treat as an allowlist
        if tool_name not in policy.allowed_tools:
            return False
    return True


def evaluate_structured_output(
    policy: StructuredOutputGatePolicy,
    model_output: str,
    tool_name: Optional[str] = None,
) -> GateDecision:
    """
    Apply a StructuredOutputGatePolicy to a model output string.
    Returns a GateDecision.
    """

    text = model_output.strip()

    # 0. Tool permission gate (only if caller supplies a tool_name)
    if tool_name is not None:
        if not _tool_is_allowed(policy, tool_name):
            return GateDecision.deny(reason="Tool permission not granted.")

    # 1. Codeblock rule
    if not policy.allow_codeblock and _contains_codeblock(text):
        return GateDecision.deny(reason="Code blocks are not allowed under this policy.")

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
            return GateDecision.deny(reason="LENIENT mode: could not extract valid JSON.")

    # 4. If we reached here, we passed
    return GateDecision.allow(notes="Structured output accepted under policy.")
