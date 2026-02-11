from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin, sqrt
from typing import Any, Dict, List, Optional, Tuple


Decision = str  # "ALLOW" | "ALLOW_WITH_CORRECTIONS" | "DENY" | "DENY_REQUIRE_ANCHOR" | "DENY_REQUIRE_RECOVERY"


@dataclass
class BowditchResult:
    decision: Decision
    misclosure: Dict[str, float]
    tolerance_used: Dict[str, float]
    corrections_applied: bool
    corrected_segments: Optional[List[Dict[str, Any]]]
    audit_report: Dict[str, Any]


def _safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    return d.get(key, default)


def _norm(fN: float, fE: float) -> float:
    return sqrt((fN * fN) + (fE * fE))


def _compute_increments(seg: Dict[str, Any]) -> Tuple[float, float]:
    """
    Convention in spec:
      lat = ΔN = L*cos(theta)
      dep = ΔE = L*sin(theta)
    theta in radians.
    """
    L = float(seg["length"])
    theta = float(seg["bearing_rad"])
    dN = L * cos(theta)
    dE = L * sin(theta)
    return dN, dE


def _segment_weight(seg: Dict[str, Any]) -> float:
    """
    Spec default:
      w_i = L_i * trust_weight * (1/risk_weight)
    """
    L = float(seg["length"])
    trust = float(_safe_get(seg, "trust_weight", 1.0))
    risk = float(_safe_get(seg, "risk_weight", 1.0))
    if risk <= 0:
        risk = 1.0
    return L * trust * (1.0 / risk)


def _tighten_tolerance_if_frog(loop_tol: Dict[str, float], tighter_multiplier: float) -> Dict[str, float]:
    return {
        "lat": float(loop_tol["lat"]) * tighter_multiplier,
        "dep": float(loop_tol["dep"]) * tighter_multiplier,
        "norm": float(loop_tol["norm"]) * tighter_multiplier,
    }


def evaluate_bowditch(
    spec: Dict[str, Any],
    given: Dict[str, Any],
) -> BowditchResult:
    """
    Minimal v0.3 evaluator:
      - compute misclosure
      - frog rule (tighten tolerance + require redundancy)
      - anchor conflict -> DENY_REQUIRE_ANCHOR
      - if within tol -> ALLOW
      - else bowditch corrections -> check safety -> ALLOW_WITH_CORRECTIONS or DENY_REQUIRE_RECOVERY
    """

    policy = spec.get("policy_semantics", {})
    frog_rule = policy.get("frog_node_rule", {})
    anchor_rule = policy.get("anchor_rule", {})
    recovery_rule = policy.get("recovery_rule", {})
    correction_safety = policy.get("correction_safety", {})

    tighter_multiplier = float(_safe_get(frog_rule, "tighter_multiplier", 1.0))
    required_redundancy = int(_safe_get(frog_rule, "required_redundancy", 0))
    max_fraction_of_segment = float(_safe_get(correction_safety, "max_fraction_of_segment", 0.02))
    max_norm_multiplier = float(_safe_get(correction_safety, "max_norm_multiplier_over_tolerance", 2.0))

    segments_list = given.get("segments", [])
    loops_list = given.get("loops", [])
    anchors = given.get("anchors", {}) or {}
    redundancy = int(_safe_get(given, "redundancy", 999999))  # default "enough"

    # Anchor conflict: allow "observed_anchor_disagreement" field (as in golden tests)
    observed_anchor_disagreement = _safe_get(anchors, "observed_anchor_disagreement", None)
    anchor_tol = float(_safe_get(anchors, "anchor_agreement_tolerance", 0.0))
    if observed_anchor_disagreement is not None and anchor_tol > 0:
        if float(observed_anchor_disagreement) > anchor_tol:
            audit = {
                "reason": "anchor conflict beyond tolerance",
                "observed_anchor_disagreement": float(observed_anchor_disagreement),
                "anchor_agreement_tolerance": anchor_tol,
                "decision": anchor_rule.get("decision", "DENY_REQUIRE_ANCHOR"),
            }
            return BowditchResult(
                decision=anchor_rule.get("decision", "DENY_REQUIRE_ANCHOR"),
                misclosure={"f_N": 0.0, "f_E": 0.0, "norm": 0.0},
                tolerance_used={"lat": 0.0, "dep": 0.0, "norm": 0.0},
                corrections_applied=False,
                corrected_segments=None,
                audit_report=audit,
            )

    # Map segments by id
    seg_by_id: Dict[str, Dict[str, Any]] = {s["segment_id"]: s for s in segments_list}

    if not loops_list:
        # No loops => no closure check; in this minimal evaluator we just allow.
        return BowditchResult(
            decision="ALLOW",
            misclosure={"f_N": 0.0, "f_E": 0.0, "norm": 0.0},
            tolerance_used={"lat": 0.0, "dep": 0.0, "norm": 0.0},
            corrections_applied=False,
            corrected_segments=None,
            audit_report={"note": "no loops provided; closure check skipped", "decision": "ALLOW"},
        )

    # For v0.3 MVP, evaluate the first loop only (keeps it bounded)
    loop = loops_list[0]
    loop_id = loop["loop_id"]
    loop_tol = loop.get("closure_tolerance", {"lat": 0.0, "dep": 0.0, "norm": 0.0})

    loop_segment_ids = loop.get("segments", [])
    loop_segments = [seg_by_id[sid] for sid in loop_segment_ids if sid in seg_by_id]

    has_frog = any(bool(_safe_get(s, "is_frog", False)) for s in loop_segments)
    tol_used = {
        "lat": float(loop_tol["lat"]),
        "dep": float(loop_tol["dep"]),
        "norm": float(loop_tol["norm"]),
    }
    frog_flags: List[str] = []

    if has_frog:
        tol_used = _tighten_tolerance_if_frog(tol_used, tighter_multiplier)
        frog_flags.append("frog_present")
        if redundancy < required_redundancy:
            audit = {
                "loop_id": loop_id,
                "frog_rule": "redundancy insufficient",
                "required_redundancy": required_redundancy,
                "provided_redundancy": redundancy,
                "decision": "DENY_REQUIRE_ANCHOR",
            }
            return BowditchResult(
                decision="DENY_REQUIRE_ANCHOR",
                misclosure={"f_N": 0.0, "f_E": 0.0, "norm": 0.0},
                tolerance_used=tol_used,
                corrections_applied=False,
                corrected_segments=None,
                audit_report=audit,
            )

    # Misclosure: sum of increments around loop
    fN = 0.0
    fE = 0.0
    increments: Dict[str, Tuple[float, float]] = {}
    for seg in loop_segments:
        dN, dE = _compute_increments(seg)
        increments[seg["segment_id"]] = (dN, dE)
        fN += dN
        fE += dE

    f = _norm(fN, fE)

    audit_base = {
        "loop_id": loop_id,
        "has_frog": has_frog,
        "frog_flags": frog_flags,
        "misclosure": {"f_N": fN, "f_E": fE, "norm": f},
        "tolerance_used": tol_used,
    }

    # If already within tolerance -> ALLOW
    if abs(fN) <= tol_used["lat"] and abs(fE) <= tol_used["dep"] and f <= tol_used["norm"]:
        audit = {**audit_base, "decision": "ALLOW", "note": "within tolerance; no correction needed"}
        return BowditchResult(
            decision="ALLOW",
            misclosure={"f_N": fN, "f_E": fE, "norm": f},
            tolerance_used=tol_used,
            corrections_applied=False,
            corrected_segments=None,
            audit_report=audit,
        )

    # If wildly beyond tolerance -> recovery (hard guardrail)
    if tol_used["norm"] > 0 and f > (max_norm_multiplier * tol_used["norm"]):
        audit = {
            **audit_base,
            "decision": recovery_rule.get("decision", "DENY_REQUIRE_RECOVERY"),
            "reason": "misclosure norm too large relative to tolerance",
            "max_norm_multiplier_over_tolerance": max_norm_multiplier,
        }
        return BowditchResult(
            decision=recovery_rule.get("decision", "DENY_REQUIRE_RECOVERY"),
            misclosure={"f_N": fN, "f_E": fE, "norm": f},
            tolerance_used=tol_used,
            corrections_applied=False,
            corrected_segments=None,
            audit_report=audit,
        )

    # Bowditch corrections
    weights = {seg["segment_id"]: _segment_weight(seg) for seg in loop_segments}
    W = sum(weights.values()) if weights else 0.0
    if W <= 0:
        W = float(len(loop_segments)) if loop_segments else 1.0

    corrected: List[Dict[str, Any]] = []
    corrections_detail: List[Dict[str, Any]] = []
    corrections_too_large = False

    for seg in loop_segments:
        sid = seg["segment_id"]
        wi = weights.get(sid, 1.0)
        cN = -fN * (wi / W)
        cE = -fE * (wi / W)

        # safety: correction magnitude must not exceed fraction of segment length
        L = float(seg["length"])
        if L > 0:
            if abs(cN) > (max_fraction_of_segment * L) or abs(cE) > (max_fraction_of_segment * L):
                corrections_too_large = True

        dN, dE = increments[sid]
        dN2 = dN + cN
        dE2 = dE + cE

        corrections_detail.append({"segment_id": sid, "cN": cN, "cE": cE, "w": wi})
        corrected.append(
            {
                **seg,
                "_unadjusted": {"dN": dN, "dE": dE},
                "_correction": {"cN": cN, "cE": cE},
                "_adjusted": {"dN": dN2, "dE": dE2},
            }
        )

    if corrections_too_large:
        audit = {
            **audit_base,
            "decision": recovery_rule.get("decision", "DENY_REQUIRE_RECOVERY"),
            "reason": "corrections exceed max_fraction_of_segment",
            "max_fraction_of_segment": max_fraction_of_segment,
            "corrections": corrections_detail,
        }
        return BowditchResult(
            decision=recovery_rule.get("decision", "DENY_REQUIRE_RECOVERY"),
            misclosure={"f_N": fN, "f_E": fE, "norm": f},
            tolerance_used=tol_used,
            corrections_applied=False,
            corrected_segments=None,
            audit_report=audit,
        )

    # Recompute misclosure after correction (should be ~0)
    fN2 = 0.0
    fE2 = 0.0
    for seg in corrected:
        fN2 += float(seg["_adjusted"]["dN"])
        fE2 += float(seg["_adjusted"]["dE"])
    f2 = _norm(fN2, fE2)

    decision: Decision = "ALLOW_WITH_CORRECTIONS"
    audit = {
        **audit_base,
        "decision": decision,
        "corrections": corrections_detail,
        "post_misclosure": {"f_N": fN2, "f_E": fE2, "norm": f2},
        "note": "bowditch corrections applied",
    }

    return BowditchResult(
        decision=decision,
        misclosure={"f_N": fN, "f_E": fE, "norm": f},
        tolerance_used=tol_used,
        corrections_applied=True,
        corrected_segments=corrected,
        audit_report=audit,
    )
