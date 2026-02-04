import argparse
from pathlib import Path

from .engine import RouteGuardEngine
from .models import GateDecision


def main():
    parser = argparse.ArgumentParser(description="RouteGuard CLI")
    parser.add_argument(
        "--policy",
        required=True,
        help="Path to structured output gate policy JSON file",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to file containing model output to evaluate",
    )
    parser.add_argument(
        "--tool",
        required=False,
        help="Optional tool name to enforce tool permission rules",
    )

    args = parser.parse_args()

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

    # NOTE: engine now returns GateResult, not GateDecision
    result = engine.evaluate_output(
        model_output,
        tool_name=args.tool,
    )

    decision = result.decision

    if decision == GateDecision.ALLOW:
        print("✅ ALLOW: Output passed RouteGuard policy.")

    elif decision == GateDecision.DENY:
        msg = "❌ DENY: Output violated RouteGuard policy."
        if result.violation and result.violation.reason:
            msg += f"\nReason: {result.violation.reason}"
        if result.violation and result.violation.detail:
            msg += f"\nDetail: {result.violation.detail}"
        print(msg)

    else:
        print(f"⚠️ RESULT: {decision}")


if __name__ == "__main__":
    main()
