import math
from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from .schemas import Decision, ExpectedDecision, ExpectedRaise, Raise, Spot

Ctx = EvaluatorContext[Spot, Decision, ExpectedDecision]


SIZE_SIGMA = 0.25  # fractional error at which the score has fallen to 1/e (~0.37)
PASS_SCORE = 0.5  # a raise counts as correct at ~20% off target or closer


def _size_score(output: Raise, expected: ExpectedRaise) -> float:
    """Gaussian falloff on % difference from the target: 1.0 exact, ~0.85 at 10% off, ~0.53 at 20%, ~0.08 at 40%."""
    rel_err = abs(output.raise_to_bb - expected.raise_to_target) / expected.raise_to_target
    return math.exp(-((rel_err / SIZE_SIGMA) ** 2))


@dataclass
class ActionMatches(Evaluator[Spot, Decision, ExpectedDecision]):
    """Fold/call/raise matches the expected action."""

    def evaluate(self, ctx: Ctx) -> bool:
        return ctx.output.action == ctx.expected_output.action


@dataclass
class RaiseSizeScore(Evaluator[Spot, Decision, ExpectedDecision]):
    """When the expected action is raise, 0-1 score for how close the raise size is to the target (0 if not a raise)."""

    def evaluate(self, ctx: Ctx) -> dict[str, float]:
        expected, output = ctx.expected_output, ctx.output
        if not isinstance(expected, ExpectedRaise):
            return {}  # not applicable
        return {'raise_size_score': _size_score(output, expected) if isinstance(output, Raise) else 0.0}


@dataclass
class DecisionCorrect(Evaluator[Spot, Decision, ExpectedDecision]):
    """Overall pass: right action and, for raises, a size scoring at least PASS_SCORE."""

    def evaluate(self, ctx: Ctx) -> bool:
        expected, output = ctx.expected_output, ctx.output
        if isinstance(expected, ExpectedRaise):
            return isinstance(output, Raise) and _size_score(output, expected) >= PASS_SCORE
        return output.action == expected.action


EVALUATOR_TYPES = [ActionMatches, RaiseSizeScore, DecisionCorrect]
