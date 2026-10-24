from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Spot(BaseModel):
    """A preflop decision point, from hero's perspective."""

    game: str = Field(description='Game format, e.g. "6-max NLHE cash".')
    effective_stack_bb: float
    hero_position: Literal['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB']
    hero_hand: str = Field(description='Hole cards, e.g. "AhKs".')
    action_before_hero: list[str] = Field(
        default_factory=list,
        description='Actions so far, in order, e.g. ["UTG raises to 2.5bb", "HJ folds"].',
    )


class Fold(BaseModel):
    reasoning: str = Field(description='One or two sentences explaining the decision.')
    action: Literal['fold'] = 'fold'


class Call(BaseModel):
    reasoning: str = Field(description='One or two sentences explaining the decision.')
    action: Literal['call'] = 'call'


class Raise(BaseModel):
    reasoning: str = Field(description='One or two sentences explaining the decision.')
    action: Literal['raise'] = 'raise'
    raise_to_bb: float = Field(description='Total bet size in big blinds after raising.')


Decision = Annotated[Fold | Call | Raise, Field(discriminator='action')]
"""The model's preflop decision, discriminated on `action`."""


class ExpectedFold(BaseModel):
    action: Literal['fold'] = 'fold'


class ExpectedCall(BaseModel):
    action: Literal['call'] = 'call'


class ExpectedRaise(BaseModel):
    """A raise is scored by how close its size is to `raise_to_target` (bb)."""

    action: Literal['raise'] = 'raise'
    raise_to_target: float = Field(gt=0)


ExpectedDecision = Annotated[ExpectedFold | ExpectedCall | ExpectedRaise, Field(discriminator='action')]
"""Ground truth for a case, discriminated on `action`; only raises carry an extra field (the target size)."""
