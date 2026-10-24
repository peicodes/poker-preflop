from typing import Literal

from pydantic import BaseModel, Field, model_validator


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


class Decision(BaseModel):
    """The model's preflop decision."""

    reasoning: str = Field(description='One or two sentences explaining the decision.')
    action: Literal['fold', 'call', 'raise']
    raise_to_bb: float | None = Field(
        default=None,
        description='Total bet size in big blinds after raising. Required for "raise", null otherwise.',
    )

    @model_validator(mode='after')
    def _check_raise_size(self) -> 'Decision':
        if self.action == 'raise' and self.raise_to_bb is None:
            raise ValueError('raise_to_bb is required when action is "raise"')
        if self.action != 'raise' and self.raise_to_bb is not None:
            raise ValueError('raise_to_bb must be null unless action is "raise"')
        return self


class ExpectedDecision(BaseModel):
    """Ground truth for a case. A raise is correct if its size falls in [raise_to_min, raise_to_max]."""

    action: Literal['fold', 'call', 'raise']
    raise_to_min: float | None = None
    raise_to_max: float | None = None
