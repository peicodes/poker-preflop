"""Smoke test: one preflop decision through the Claude Code CLI. Usage: python smoke_test.py [model]"""

import sys

from poker_preflop.agent import build_agent, render_spot
from poker_preflop.schemas import Spot

spot = Spot(
    game='6-max NLHE cash',
    effective_stack_bb=100,
    hero_position='BTN',
    hero_hand='7h2c',
    action_before_hero=['UTG folds', 'HJ folds', 'CO folds'],
)
agent = build_agent(model=sys.argv[1] if len(sys.argv) > 1 else 'sonnet')
result = agent.run_sync(render_spot(spot))
print(result.output)
print(result.usage)
