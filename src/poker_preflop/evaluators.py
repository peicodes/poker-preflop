import math
from dataclasses import dataclass
from functools import cache

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from .agent import build_model, render_spot
from .schemas import Decision, ExpectedDecision, ExpectedRaise, Raise, Spot

Ctx = EvaluatorContext[Spot, Decision, ExpectedDecision]


SIZE_SIGMA = 0.25  # fractional error at which the size score has fallen to 1/e (~0.37)


def _size_score(output: Raise, expected: ExpectedRaise) -> float:
    """Gaussian falloff on % difference from the target: 1.0 exact, ~0.85 at 10% off, ~0.53 at 20%, ~0.08 at 40%."""
    rel_err = abs(output.raise_to_bb - expected.raise_to_target) / expected.raise_to_target
    return math.exp(-((rel_err / SIZE_SIGMA) ** 2))


@dataclass
class Correctness(Evaluator[Spot, Decision, ExpectedDecision]):
    """0-1 score: 0 if the action is wrong; 1 for a right fold/call; for a right raise, how close the size is to the target."""

    def evaluate(self, ctx: Ctx) -> float:
        expected, output = ctx.expected_output, ctx.output
        if output.action != expected.action:
            return 0.0
        if isinstance(expected, ExpectedRaise) and isinstance(output, Raise):
            return _size_score(output, expected)
        return 1.0


JUDGE_MODEL = 'gateway/google-ai-studio:gemini-3.8-flash'  # claude-code models can't do structured output


class ReasoningVerdict(BaseModel):
    consistent: bool = Field(
        description='True if the reasoning supports the chosen action, e.g. not folding while calling the hand strong.'
    )
    consistent_reason: str = Field(description='One sentence.')
    raise_size_justified: bool | None = Field(
        description='Only for raises: True if the reasoning gives a rationale for the raise size; null for fold/call.'
    )
    raise_size_reason: str | None = Field(description='One sentence; null for fold/call.')


@cache
def _judge() -> Agent[None, ReasoningVerdict]:
    return Agent(
        build_model(JUDGE_MODEL),
        output_type=ReasoningVerdict,
        instructions=(
            "You grade a poker player's written reasoning, not whether the decision is right. Check two things:\n"
            '1. consistent: does the reasoning argue for the action that was actually taken? Fail if it contradicts it '
            '(e.g. action is fold but the reasoning says the hand is very strong, or action is raise but it argues the hand is weak).\n'
            '2. raise_size_justified: only if the action is raise, does the reasoning say why that particular size was chosen '
            '(e.g. position, the opener\'s size, stack depth, wanting folds or value)? Merely saying "raise" or "standard sizing" '
            'with no reasoning about the size fails. For fold/call set this and its reason to null.'
        ),
    )


@dataclass
class Reasoning(Evaluator[Spot, Decision, ExpectedDecision]):
    """LLM judge of the `reasoning` text: it must support the action taken and, for raises, justify the size."""

    async def evaluate(self, ctx: Ctx) -> EvaluationReason:
        prompt = f'{render_spot(ctx.inputs)}\n\nPlayer output:\n{ctx.output.model_dump_json(indent=2)}'
        verdict = (await _judge().run(prompt)).output
        passed, reasons = verdict.consistent, [verdict.consistent_reason]
        if isinstance(ctx.output, Raise):
            passed = passed and bool(verdict.raise_size_justified)
            reasons.append(verdict.raise_size_reason or 'No rationale given for the raise size.')
        return EvaluationReason(passed, ' '.join(reasons))


EVALUATOR_TYPES = [Correctness, Reasoning]
