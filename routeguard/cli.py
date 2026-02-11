import argparse
from pathlib import Path

from .engine import RouteGuardEngine
from .models import GateDecision

from .golden import run_bowditch_golden


def main():
    parser = argparse.ArgumentParser(description="RouteGuard CLI")

    sub = parser.add_subparsers(dest="cmd", required=True)

    # -------------------------
    # structured-output gate
    # -------------------------
    p_struct = sub.add_parser("structured", help="Evaluate structured output against a policy")
    p_struct.add_argument("--policy", required=True, help="Path to structured output gate policy JSON file")
    p_struct.add_argument("--file", required=True, help="Path to file containing model output to evaluate")

    # -------------------------
    # bowditch golden tests
    # -------------------------
    p_bow = sub.add_parser("bowditch-golden", help="Run golden tests from Bowditch v0.3 spec JSON")
    p_bow.add_argument("--spec", required=True, help="Path to Bowditch v0.3 spec JSON (with golden_tests)")
    p_bow.add_argument("--json", action="store_true", help="Print full JSON report")

    args = parser.parse_args()

    if args.cmd == "structured":
        policy_path = Path(args.policy)
        output_path = Path(args.file)

        if not policy_path.exists():
            print(f"Policy file not found: {policy_path}")
            return

        if not output_path.exists():
            print(f"Output file not found: {output_path}")
            return

        engine = RouteGuardEngine(str(policy_path))
        model_output = output_path.read_text(encoding="utf-8")
        decision = engine.evaluate_output(model_output)

        if decision == GateDecision.ALLOW:
            print("✅ ALLOW: Output passed RouteGuard policy.")
        elif decision == GateDecision.DENY:
            print("❌ DENY: Output violated RouteGuard policy.")
        else:
            print(f"⚠️ RESULT: {decision}")
        return

    if args.cmd == "bowditch-golden":
        spec_path = Path(args.spec)
        if not spec_path.exists():
            print(f"Spec file not found: {spec_path}")
            return

        failures, report = run_bowditch_golden(str(spec_path))

        if args.json:
            import json

            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(f"Golden tests: {report['total']} | Failures: {report['failures']}")
            for r in report["results"]:
                print(f"- {r['status']}: {r['test_id']}")

        raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
