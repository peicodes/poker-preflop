import os
from pathlib import Path

from pydantic_ai import Agent, PromptedOutput
from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from .claude_code_model import claude_code_model
from .schemas import Decision, Spot

PROMPTS_DIR = Path(__file__).parents[2] / 'prompts'


GATEWAY_GOOGLE_PREFIX = 'gateway/google-ai-studio:'


def build_model(model: str) -> Model:
    """`gateway/google-ai-studio:<model>` goes through the Logfire (Pydantic AI) Gateway;
    anything else is a Claude Code model name (`sonnet`, `opus`, ...)."""
    if not model.startswith(GATEWAY_GOOGLE_PREFIX):
        return claude_code_model(model)
    base_url = os.getenv('PYDANTIC_AI_GATEWAY_BASE_URL', 'https://gateway-us.pydantic.dev/proxy').rstrip('/')
    provider = GoogleProvider(
        api_key=os.environ['PYDANTIC_AI_GATEWAY_API_KEY'],
        base_url=f'{base_url}/google-ai-studio',
    )
    return GoogleModel(model.removeprefix(GATEWAY_GOOGLE_PREFIX), provider=provider)


def build_agent(prompt: str = 'v1', model: str = 'sonnet') -> Agent[None, Decision]:
    """`prompt` is a file name in prompts/ (without .md)."""
    instructions = (PROMPTS_DIR / f'{prompt}.md').read_text()
    return Agent(
        build_model(model),
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
