import random

from game.card import Card


class Deck:
    def __init__(self) -> None:
        self.cards: list[Card] = []
        self.reset()

    def reset(self) -> None:
        suits = ("Hearts", "Diamonds", "Clubs", "Spades")
        self.cards = [Card(rank, suit) for suit in suits for rank in range(2, 15)]

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def draw(self) -> Card:
        if not self.cards:
            raise ValueError("Cannot draw from an empty deck.")

        return self.cards.pop()
