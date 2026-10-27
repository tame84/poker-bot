from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    rank: int
    suit: str
