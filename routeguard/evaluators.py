from typing import Optional
import json

from .models import StructuredOutputGatePolicy, GateMode, GateDecision


def _contains_codeblock(text: str) -> bool:
    return "```" in text


def _looks_like_wrapped_json(text: str) -> bool:
    stripped = text.strip()
    if not stripped.startswith("{"):
        return True
    if not stripped.endswith("}"):
        return True
    return False


def _is_valid_json(text: str) -> bool:
    try:
        obj = json.loads(text)
        return isinstance(obj, dict)
    except Exception:
        return False


def evaluate_structured_output(
    policy: StructuredOutputGatePolicy,
    model_output: str,
    tool_name: Optional[str] = None,
) -> GateDecision:
    text = model_output.strip()

    # Tool permission enforcement
    if tool_name:
        if policy.forbidden_tools and tool_name in policy.forbidden_tools:
            return GateDecision.DENY
        if policy.allowed_tools and tool_name not in policy.allowed_tools:
            return GateDecision.DENY

    # Codeblock rule
    if not policy.allow_codeblock and _contains_codeblock(text):
        return GateDecision.DENY

    # STRICT mode
    if policy.mode == GateMode.STRICT:
        if _looks_like_wrapped_json(text):
            return GateDecision.DENY
        if not _is_valid_json(text):
            return GateDecision.DENY

    # LENIENT mode
    if policy.mode == GateMode.LENIENT:
        extracted = None
        try:
            extracted = json.loads(text)
        except Exception:
            if policy.allow_substring_extraction:
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    candidate = text[start:end+1]
                    try:
                        extracted = json.loads(candidate)
                    except Exception:
                        extracted = None

        if extracted is None:
            return GateDecision.DENY

    return GateDecision.ALLOW
