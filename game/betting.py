from dataclasses import dataclass, field
from enum import StrEnum, auto


class Action(StrEnum):
    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    RAISE = auto()


@dataclass
class BettingRound:
    highest_bet: int = 0
    min_raise: int = 20
    pending: set[int] = field(default_factory=set)
