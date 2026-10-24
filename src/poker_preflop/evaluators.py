from dataclasses import dataclass

from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from .schemas import Decision, ExpectedDecision, Spot


def _size_in_range(output: Decision, expected: ExpectedDecision) -> bool:
    lo = expected.raise_to_min if expected.raise_to_min is not None else float('-inf')
    hi = expected.raise_to_max if expected.raise_to_max is not None else float('inf')
    return lo <= output.raise_to_bb <= hi


@dataclass
class ActionMatches(Evaluator[Spot, Decision, ExpectedDecision]):
    """Fold/call/raise matches the expected action."""

    def evaluate(self, ctx: EvaluatorContext[Spot, Decision, ExpectedDecision]) -> bool:
        expected = ctx.metadata
        return ctx.output.action == expected.action


@dataclass
class RaiseSizeInRange(Evaluator[Spot, Decision, ExpectedDecision]):
    """When both expected and actual action are raise, the size falls in the expected range."""

    def evaluate(self, ctx: EvaluatorContext[Spot, Decision, ExpectedDecision]) -> dict[str, bool]:
        expected = ctx.metadata
        if expected.action != 'raise' or ctx.output.action != 'raise':
            return {}  # not applicable
        return {'raise_size_in_range': _size_in_range(ctx.output, expected)}


@dataclass
class DecisionCorrect(Evaluator[Spot, Decision, ExpectedDecision]):
    """Overall pass: right action and, for raises, an acceptable size."""

    def evaluate(self, ctx: EvaluatorContext[Spot, Decision, ExpectedDecision]) -> bool:
        expected = ctx.metadata
        if ctx.output.action != expected.action:
            return False
        if expected.action != 'raise':
            return True
        return _size_in_range(ctx.output, expected)


EVALUATOR_TYPES = [ActionMatches, RaiseSizeInRange, DecisionCorrect]
