from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from .schemas import Decision, ExpectedDecision, ExpectedRaise, Raise, Spot

Ctx = EvaluatorContext[Spot, Decision, ExpectedDecision]


def _size_in_range(output: Raise, expected: ExpectedRaise) -> bool:
    lo = expected.raise_to_min if expected.raise_to_min is not None else float('-inf')
    hi = expected.raise_to_max if expected.raise_to_max is not None else float('inf')
    return lo <= output.raise_to_bb <= hi


@dataclass
class ActionMatches(Evaluator[Spot, Decision, ExpectedDecision]):
    """Fold/call/raise matches the expected action."""

    def evaluate(self, ctx: Ctx) -> bool:
        return ctx.output.action == ctx.expected_output.action


@dataclass
class RaiseSizeInRange(Evaluator[Spot, Decision, ExpectedDecision]):
    """When both expected and actual action are raise, the size falls in the range given by the expected output."""

    def evaluate(self, ctx: Ctx) -> dict[str, bool]:
        expected, output = ctx.expected_output, ctx.output
        if not isinstance(expected, ExpectedRaise) or not isinstance(output, Raise):
            return {}  # not applicable
        return {'raise_size_in_range': _size_in_range(output, expected)}


@dataclass
class DecisionCorrect(Evaluator[Spot, Decision, ExpectedDecision]):
    """Overall pass: right action and, for raises, a size within the expected range."""

    def evaluate(self, ctx: Ctx) -> bool:
        expected, output = ctx.expected_output, ctx.output
        if isinstance(expected, ExpectedRaise):
            return isinstance(output, Raise) and _size_in_range(output, expected)
        return output.action == expected.action


EVALUATOR_TYPES = [ActionMatches, RaiseSizeInRange, DecisionCorrect]
