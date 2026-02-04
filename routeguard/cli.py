import argparse
from pathlib import Path

from .engine import RouteGuardEngine
from .models import GateDecision


def main():
    parser = argparse.ArgumentParser(description="RouteGuard CLI")
    parser.add_argument("--policy", required=True, help="Path to policy JSON file")
    parser.add_argument("--file", required=True, help="Path to file containing model output")
    parser.add_argument("--tool", required=False, help="Optional tool name to enforce tool permission rules")

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

    # Engine returns GateDecision enum directly
    decision = engine.evaluate_output(model_output, tool_name=args.tool)

    if decision == GateDecision.ALLOW:
        print("✅ ALLOW: Output passed RouteGuard policy.")
    elif decision == GateDecision.DENY:
        print("❌ DENY: Output violated RouteGuard policy.")
    elif decision == GateDecision.REPAIR:
        print("🛠️ REPAIR: Output requires repair under RouteGuard policy.")
    else:
        print(f"⚠️ RESULT: {decision}")


if __name__ == "__main__":
    main()
