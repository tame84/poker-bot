from dataclasses import dataclass, field
from enum import Enum, auto

from game.betting import Action, BettingRound
from game.card import Card
from game.deck import Deck
from game.player import Player


class Phase(Enum):
    PREFLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    SHOWDOWN = auto()
    FINISHED = auto()


@dataclass
class PokerGame:
    players: list[Player]
    small_blind: int = 10
    big_blind: int = 20
    deck: Deck = field(default_factory=Deck)
    community_cards: list[Card] = field(default_factory=list)
    betting: BettingRound = field(default_factory=BettingRound)
    pot: int = 0
    dealer_index: int = -1
    current_player_index: int | None = None
    winner_index: int | None = None
    phase: Phase = Phase.PREFLOP
    hand_started: bool = False

    def start_hand(self) -> None:
        if len(self.players) != 3:
            raise ValueError("This game only supports 3 players.")
        if self.hand_started and self.phase != Phase.FINISHED:
            raise RuntimeError("Finish the current hand before starting a new one.")
        if not 0 < self.small_blind < self.big_blind:
            raise ValueError("Invalid blinds.")
        if any(player.stack <= self.big_blind for player in self.players):
            raise ValueError("Not enough chips. All-ins are not supported.")

        self.deck.reset()
        self.deck.shuffle()
        self.community_cards.clear()
        self.pot = 0
        self.winner_index = None

        self.dealer_index = (self.dealer_index + 1) % 3
        self.phase = Phase.PREFLOP
        self.hand_started = True

        for player in self.players:
            player.reset_for_hand()

        sb = (self.dealer_index + 1) % 3
        bb = (self.dealer_index + 2) % 3

        for _ in range(2):
            for offset in range(3):
                index = (sb + offset) % 3
                self.players[index].hand.append(self.deck.draw())

        self._commit(sb, self.small_blind)
        self._commit(bb, self.big_blind)

        self.betting = BettingRound(self.big_blind, self.big_blind, {0, 1, 2})

        self.current_player_index = (bb + 1) % 3

    def _commit(self, player_index: int, amount: int) -> None:
        player = self.players[player_index]

        if amount < 0 or amount >= player.stack:
            raise ValueError("Not enough chips. All-ins are not supported.")

        player.stack -= amount
        player.current_bet += amount
        self.pot += amount

    def amount_to_call(self) -> int:
        if self.current_player_index is None:
            return 0

        player = self.players[self.current_player_index]
        return self.betting.highest_bet - player.current_bet

    def minimum_raise_to(self) -> int:
        return self.betting.highest_bet + self.betting.min_raise

    def maximum_raise_to(self) -> int:
        if self.current_player_index is None:
            return 0

        player = self.players[self.current_player_index]
        return player.current_bet + player.stack - 1

    def get_legal_actions(self) -> set[Action]:
        if self.current_player_index is None:
            return set()

        player = self.players[self.current_player_index]
        to_call = self.amount_to_call()
        actions = {Action.FOLD}

        if to_call == 0:
            actions.add(Action.CHECK)
        elif player.stack > to_call:
            actions.add(Action.CALL)

        if self.maximum_raise_to() >= self.minimum_raise_to():
            actions.add(Action.RAISE)

        return actions

    def apply_action(self, action: Action, amount: int | None = None) -> None:
        if not self.hand_started or self.current_player_index is None:
            raise ValueError("No player can act at the moment.")

        if not isinstance(action, Action) or action not in self.get_legal_actions():
            raise ValueError(f"Illegal action: {action}")

        if action == Action.RAISE and (
            type(amount) is not int
            or not self.minimum_raise_to() <= amount <= self.maximum_raise_to()
        ):
            raise ValueError("Illegal raise amount.")

        player_index = self.current_player_index
        player = self.players[player_index]
        self.betting.pending.remove(player_index)

        if action == Action.FOLD:
            player.folded = True

        elif action == Action.CALL:
            self._commit(player_index, self.amount_to_call())

        elif action == Action.RAISE:
            old_highest = self.betting.highest_bet

            assert amount is not None
            self._commit(player_index, amount - player.current_bet)

            self.betting.highest_bet = amount
            self.betting.min_raise = amount - old_highest

            self.betting.pending = {
                i
                for i, p in enumerate(self.players)
                if not p.folded and i != player_index
            }

        active = [i for i, p in enumerate(self.players) if not p.folded]

        if len(active) == 1:
            self._award_pot(active[0])
        elif not self.betting.pending:
            self._finish_betting_round()
        else:
            self.current_player_index = next(
                (player_index + step) % 3
                for step in range(1, 4)
                if (player_index + step) % 3 in self.betting.pending
            )

    def _finish_betting_round(self) -> None:
        if self.phase == Phase.RIVER:
            self.phase = Phase.SHOWDOWN
            self.current_player_index = None
            return

        self.deck.draw()

        if self.phase == Phase.PREFLOP:
            self.community_cards.extend(self.deck.draw() for _ in range(3))
            self.phase = Phase.FLOP

        elif self.phase == Phase.FLOP:
            self.community_cards.append(self.deck.draw())
            self.phase = Phase.TURN

        elif self.phase == Phase.TURN:
            self.community_cards.append(self.deck.draw())
            self.phase = Phase.RIVER

        for player in self.players:
            player.current_bet = 0

        self.betting = BettingRound(
            min_raise=self.big_blind,
            pending={i for i, p in enumerate(self.players) if not p.folded},
        )

        self.current_player_index = next(
            (self.dealer_index + step) % 3
            for step in range(1, 4)
            if (self.dealer_index + step) % 3 in self.betting.pending
        )

    def award_showdown(self, winner_index: int) -> None:
        if self.phase != Phase.SHOWDOWN:
            raise ValueError("Not a showdown.")

        if winner_index not in range(3) or self.players[winner_index].folded:
            raise ValueError("The winner must be an active player.")

        self._award_pot(winner_index)

    def _award_pot(self, winner_index: int) -> None:
        self.players[winner_index].stack += self.pot
        self.pot = 0
        self.winner_index = winner_index
        self.phase = Phase.FINISHED
        self.current_player_index = None
        self.betting.pending.clear()
