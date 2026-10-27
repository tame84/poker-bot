import random
import unittest

from game.betting import Action
from game.deck import Deck
from game.game import Phase, PokerGame
from game.player import Player


def new_game() -> PokerGame:
    game = PokerGame([Player("A"), Player("B"), Player("C")])
    game.start_hand()
    return game


class PokerGameTests(unittest.TestCase):
    def test_deck_is_unique(self) -> None:
        deck = Deck()

        self.assertEqual(len(deck.cards), 52)
        self.assertEqual(len(set(deck.cards)), 52)

    def test_blinds_and_turn_order(self) -> None:
        game = new_game()

        self.assertEqual(game.dealer_index, 0)
        self.assertEqual(game.current_player_index, 0)
        self.assertEqual(game.pot, 30)

        self.assertEqual([p.stack for p in game.players], [1000, 990, 980])
        self.assertEqual([p.current_bet for p in game.players], [0, 10, 20])
        self.assertEqual(len(game.deck.cards), 46)

    def test_normal_call_to_flop(self) -> None:
        game = new_game()

        self.assertNotIn(Action.CHECK, game.get_legal_actions())

        game.apply_action(Action.CALL)  # Dealer
        self.assertEqual(game.current_player_index, 1)

        game.apply_action(Action.CALL)  # Small blind
        self.assertEqual(game.current_player_index, 2)

        self.assertEqual(game.amount_to_call(), 0)
        game.apply_action(Action.CHECK)  # Big blind

        self.assertEqual(game.phase, Phase.FLOP)
        self.assertEqual(game.pot, 60)
        self.assertEqual(len(game.community_cards), 3)
        self.assertEqual(game.current_player_index, 1)

        self.assertEqual([p.current_bet for p in game.players], [0, 0, 0])

    def test_raise_reopens_action(self) -> None:
        game = new_game()

        game.apply_action(Action.CALL)  # Dealer
        game.apply_action(Action.CALL)  # Small blind
        game.apply_action(Action.RAISE, 40)  # Big blind

        self.assertEqual(game.current_player_index, 0)
        self.assertEqual(game.minimum_raise_to(), 60)

        game.apply_action(Action.CALL)  # Dealer
        game.apply_action(Action.CALL)  # Small blind

        self.assertEqual(game.phase, Phase.FLOP)
        self.assertEqual(game.pot, 120)

    def test_raise_minimum_tracks_last_raise(self) -> None:
        game = new_game()

        game.apply_action(Action.RAISE, 60)
        self.assertEqual(game.minimum_raise_to(), 100)

        with self.assertRaises(ValueError):
            game.apply_action(Action.RAISE, 80)

        self.assertEqual(game.current_player_index, 1)
        self.assertEqual(game.pot, 90)

        game.apply_action(Action.RAISE, 100)

        self.assertEqual(game.current_player_index, 2)
        self.assertEqual(game.minimum_raise_to(), 140)

    def test_invalid_check_does_not_change_state(self) -> None:
        game = new_game()

        with self.assertRaises(ValueError):
            game.apply_action(Action.CHECK)

        self.assertEqual(game.pot, 30)
        self.assertEqual(game.betting.pending, {0, 1, 2})
        self.assertEqual(game.current_player_index, 0)

    def test_fold_awards_pot(self) -> None:
        game = new_game()

        game.apply_action(Action.CALL)
        game.apply_action(Action.CALL)
        game.apply_action(Action.CHECK)

        expected_rounds = [(Phase.TURN, 4), (Phase.RIVER, 5), (Phase.SHOWDOWN, 5)]

        for expected_phase, expected_cards in expected_rounds:
            for _ in range(3):
                game.apply_action(Action.CHECK)

            self.assertEqual(game.phase, expected_phase)
            self.assertEqual(len(game.community_cards), expected_cards)

        self.assertIsNone(game.current_player_index)

        with self.assertRaises(RuntimeError):
            game.start_hand()

        game.award_showdown(0)

        self.assertEqual(game.phase, Phase.FINISHED)
        self.assertEqual(sum(p.stack for p in game.players), 3000)

        game.start_hand()
        self.assertEqual(game.dealer_index, 1)

    def test_no_all_in_and_side_pots_yet(self) -> None:
        game = new_game()

        with self.assertRaises(ValueError):
            game.apply_action(Action.RAISE, 1000)

        self.assertEqual(game.current_player_index, 0)
        self.assertEqual(game.pot, 30)

    def test_postflop_bet_reopens_actions(self) -> None:
        game = new_game()

        game.apply_action(Action.CALL)
        game.apply_action(Action.CALL)
        game.apply_action(Action.CHECK)

        self.assertEqual(game.current_player_index, 1)

        game.apply_action(Action.CHECK)  # Small blind
        game.apply_action(Action.RAISE, 30)  # Big blind

        self.assertEqual(game.minimum_raise_to(), 60)
        self.assertEqual(game.current_player_index, 0)

        game.apply_action(Action.CALL)  # Dealer

        self.assertEqual(game.current_player_index, 1)

        game.apply_action(Action.FOLD)  # Small blind

        self.assertEqual(game.phase, Phase.TURN)
        self.assertEqual(game.pot, 120)

    def test_hundreds_of_random_single_hands(self) -> None:
        for _ in range(300):
            game = new_game()

            for _ in range(120):
                if game.phase in (Phase.FINISHED, Phase.SHOWDOWN):
                    break

                actions = sorted(game.get_legal_actions())
                choice = random.choice(actions)

                if choice == Action.RAISE:
                    game.apply_action(choice, game.minimum_raise_to())
                else:
                    game.apply_action(choice)

                self.assertEqual(sum(p.stack for p in game.players) + game.pot, 3000)

            else:
                self.fail("Hand should finish in fewer than 120 actions.")

            if game.phase == Phase.SHOWDOWN:
                winner = next(i for i, p in enumerate(game.players) if not p.folded)
                game.award_showdown(winner)

            self.assertEqual(sum(p.stack for p in game.players), 3000)


if __name__ == "__main__":
    unittest.main()
