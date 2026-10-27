from dataclasses import dataclass, field
from enum import Enum, auto

from game.card import Card
from game.deck import Deck
from game.player import Player


class Phase(Enum):
    PREFLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    SHOWDOWN = auto()


@dataclass
class PokerGame:
    players: list[Player]
    deck: Deck = field(default_factory=Deck)
    community_cards: list[Card] = field(default_factory=list)
    pot: int = 0
    dealer_index: int = -1
    phase: Phase = Phase.PREFLOP

    def start_hand(self) -> None:
        if len(self.players) != 3:
            raise ValueError("This game only supports 3 players.")

        self.deck.reset()
        self.deck.shuffle()
        self.community_cards.clear()
        self.pot = 0

        for player in self.players:
            player.reset_for_hand()

        self.dealer_index = (self.dealer_index + 1) % 3
        small_blind_index = (self.dealer_index + 1) % 3

        for _ in range(2):
            for offset in range(3):
                index = (small_blind_index + offset) % 3
                self.players[index].hand.append(self.deck.draw())

        self.phase = Phase.PREFLOP

    def advance_phase(self) -> None:
        """Demo only: reveal cards without running betting rounds"""
        if self.phase == Phase.PREFLOP:
            self.deck.draw()
            self.community_cards.extend(self.deck.draw() for _ in range(3))
            self.phase = Phase.FLOP

        elif self.phase == Phase.FLOP:
            self.deck.draw()
            self.community_cards.append(self.deck.draw())
            self.phase = Phase.TURN

        elif self.phase == Phase.TURN:
            self.deck.draw()
            self.community_cards.append(self.deck.draw())
            self.phase = Phase.RIVER

        elif self.phase == Phase.RIVER:
            self.phase = Phase.SHOWDOWN

        else:
            self.start_hand()
