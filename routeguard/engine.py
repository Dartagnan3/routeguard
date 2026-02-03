from typing import Optional

from .models import (
    StructuredOutputGatePolicy,
    GateDecision,
)
from .loaders import load_structured_output_policy
from .evaluators import evaluate_structured_output


class RouteGuardEngine:
    """
    Main orchestration engine for RouteGuard.
    Loads policies and evaluates model outputs against them.
    """

    def __init__(self, policy_path: str):
        self.policy = load_structured_output_policy(policy_path)

    def evaluate_output(self, model_output: str) -> GateDecision:
        """
        Apply the loaded policy to a model output string.
        """
        return evaluate_structured_output(self.policy, model_output)
