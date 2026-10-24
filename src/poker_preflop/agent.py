from pathlib import Path

from pydantic_ai import Agent, PromptedOutput

from .claude_code_model import claude_code_model
from .schemas import Decision, Spot

PROMPTS_DIR = Path(__file__).parents[2] / 'prompts'


def build_agent(prompt: str = 'v1', model: str = 'sonnet') -> Agent[None, Decision]:
    """`prompt` is a file name in prompts/ (without .md)."""
    instructions = (PROMPTS_DIR / f'{prompt}.md').read_text()
    return Agent(
        claude_code_model(model),
        name=f'preflop_{prompt}',
        instructions=instructions,
        output_type=PromptedOutput(Decision),
        retries=2,
    )


def render_spot(spot: Spot) -> str:
    actions = '\n'.join(f'- {a}' for a in spot.action_before_hero) or '- (none, hero is first to act)'
    return (
        f'Game: {spot.game}\n'
        f'Effective stack: {spot.effective_stack_bb:g}bb\n'
        f'Hero position: {spot.hero_position}\n'
        f'Hero hand: {spot.hero_hand}\n'
        f'Action before hero:\n{actions}'
    )
