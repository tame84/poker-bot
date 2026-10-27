from dataclasses import dataclass, field

from game.card import Card


@dataclass()
class Player:
    name: str
    stack: int = 1000
    hand: list[Card] = field(default_factory=list)
    current_bet: int = 0
    folded: bool = False
    all_in: bool = False

    def reset_for_hand(self) -> None:
        self.hand.clear()
        self.current_bet = 0
        self.folded = False
        self.all_in = False
