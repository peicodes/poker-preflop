"""Run the preflop eval.

    python run_evals.py                          # prompts/v1.md, sonnet
    python run_evals.py --prompt v2 --model opus
    python run_evals.py --model gateway/google-ai-studio:gemini-2.5-flash
"""

import argparse
import os
from pathlib import Path

import logfire
from pydantic_evals import Dataset

from poker_preflop.agent import build_agent, render_spot
from poker_preflop.evaluators import EVALUATOR_TYPES
from poker_preflop.schemas import Decision, ExpectedDecision, Spot

parser = argparse.ArgumentParser()
parser.add_argument('--prompt', default='v1', help='file name in prompts/, without .md')
parser.add_argument('--model', default='sonnet', help='`claude --model` value (Claude Code) or gateway/google-ai-studio:<model> (Logfire gateway)')
parser.add_argument('--dataset', default='datasets/preflop.yaml')
parser.add_argument('--concurrency', type=int, default=5)
args = parser.parse_args()

# Send traces to Logfire once credentials exist (`logfire auth` + `logfire projects new` in this folder).
if Path('.logfire').exists() or os.environ.get('LOGFIRE_TOKEN'):
    logfire.configure()
    logfire.instrument_pydantic_ai()

dataset = Dataset[Spot, Decision | ExpectedDecision].from_file(args.dataset, custom_evaluator_types=EVALUATOR_TYPES)
agent = build_agent(prompt=args.prompt, model=args.model)


async def decide(spot: Spot) -> Decision:
    result = await agent.run(render_spot(spot))
    return result.output


report = dataset.evaluate_sync(
    decide,
    name=f'preflop:{args.prompt}:{args.model}',
    max_concurrency=args.concurrency,
    metadata={'prompt': args.prompt, 'model': args.model},
)
report.print(include_input=False, include_output=True, include_durations=True)
