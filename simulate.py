import random

from game.betting import Action
from game.game import Phase, PokerGame
from game.player import Player


def main() -> None:
    games = 10_000

    for _ in range(games):
        game = PokerGame([Player("A"), Player("B"), Player("C")])
        game.start_hand()

        while game.phase not in (Phase.SHOWDOWN, Phase.FINISHED):
            actions = sorted(game.get_legal_actions())
            action = random.choice(actions)

            amount = game.minimum_raise_to() if action == Action.RAISE else None

            game.apply_action(action, amount)

        if game.phase == Phase.SHOWDOWN:
            winner = next(
                i for i, player in enumerate(game.players) if not player.folded
            )
            game.award_showdown(winner)

        assert sum(player.stack for player in game.players) == 3000

    print(f"{games} hands simulated successfully.")


if __name__ == "__main__":
    main()
