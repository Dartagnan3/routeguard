from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Tuple

from .bowditch import evaluate_bowditch


def load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _ok(condition: bool) -> str:
    return "PASS" if condition else "FAIL"


def run_bowditch_golden(spec_path: str) -> Tuple[int, Dict[str, Any]]:
    spec = load_json(spec_path)
    tests = spec.get("golden_tests", [])
    failures = 0
    results = []

    for t in tests:
        test_id = t.get("test_id", "unknown")
        given = t.get("given", {})
        expect = t.get("expect", {})

        out = evaluate_bowditch(spec, given)

        checks = []
        # 1) decision match
        if "decision" in expect:
            checks.append(("decision", out.decision == expect["decision"]))

        # 2) final misclosure norm <= threshold
        if "final_misclosure_norm_lte" in expect:
            # if corrections applied, we use post_misclosure; otherwise the current misclosure
            post = out.audit_report.get("post_misclosure")
            norm_val = None
            if post and "norm" in post:
                norm_val = float(post["norm"])
            else:
                norm_val = float(out.misclosure["norm"])
            checks.append(("final_misclosure_norm_lte", norm_val <= float(expect["final_misclosure_norm_lte"])))

        # 3) corrections applied expectation
        if "corrections_applied" in expect:
            checks.append(("corrections_applied", out.corrections_applied == bool(expect["corrections_applied"])))

        # 4) reason contains
        if "reason_contains" in expect:
            s = json.dumps(out.audit_report, ensure_ascii=False)
            checks.append(("reason_contains", str(expect["reason_contains"]) in s))

        passed = all(v for _, v in checks)
        if not passed:
            failures += 1

        results.append(
            {
                "test_id": test_id,
                "status": _ok(passed),
                "checks": [{"name": k, "ok": v} for k, v in checks],
                "output": out.audit_report,
            }
        )

    report = {
        "spec_path": spec_path,
        "total": len(tests),
        "failures": failures,
        "results": results,
    }
    return failures, report


def main():
    import argparse

    p = argparse.ArgumentParser(description="RouteGuard golden test runner")
    p.add_argument("--spec", required=True, help="Path to Bowditch v0.3 spec JSON (with golden_tests)")
    p.add_argument("--json", action="store_true", help="Print full JSON report")
    args = p.parse_args()

    failures, report = run_bowditch_golden(args.spec)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Golden tests: {report['total']} | Failures: {report['failures']}")
        for r in report["results"]:
            print(f"- {r['status']}: {r['test_id']}")

    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
