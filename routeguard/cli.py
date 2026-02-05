import argparse
from pathlib import Path

from .engine import RouteGuardEngine
from .models import GateDecision
from .validators import validate_against_schema


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

    model_output = output_path.read_text(encoding="utf-8")

    # 0) Schema validation (fail fast, before any policy logic)
    # NOTE: adjust this if you want a different schema entrypoint
    schema_path = Path("spec/claim_record.schema.json")
    if schema_path.exists():
        ok, err = validate_against_schema(model_output, schema_path)
        if not ok:
            print(f"❌ SCHEMA FAIL: {err}")
            return
    else:
        # If schema isn't present locally, don't block execution.
        # (Optional: you can choose to hard-fail instead.)
        print(f"⚠️ Schema not found (skipping): {schema_path}")

    # 1) Policy evaluation
    engine = RouteGuardEngine(str(policy_path))

    # If your engine returns GateResult (newer), handle that:
    result = engine.evaluate_output(model_output, tool_name=args.tool)
    decision = result.decision if hasattr(result, "decision") else result  # backward compat

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
