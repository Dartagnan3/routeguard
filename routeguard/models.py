from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, List


class GateMode(str, Enum):
    STRICT = "STRICT"
    LENIENT = "LENIENT"


class GateDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REPAIR = "REPAIR"


@dataclass
class StructuredOutputGatePolicy:
    policy_id: str
    version: str
    mode: GateMode

    allow_codeblock: bool
    allow_substring_extraction: bool
    allow_repair: bool

    # NEW: tool permission controls
    allowed_tools: Optional[List[str]] = None
    forbidden_tools: Optional[List[str]] = None

    notes: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class GateEvent:
    policy_id: str
    input_payload: Any
    output_payload: Any
    metadata: Dict[str, Any]


@dataclass
class InvariantViolation:
    reason: str
    detail: Optional[str] = None


@dataclass
class GateResult:
    decision: GateDecision
    violation: Optional[InvariantViolation] = None
    repaired_output: Optional[Any] = None
