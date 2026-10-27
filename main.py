from game.game import PokerGame
from game.player import Player
from ui.poker_ui import PokerUI


def main():
    players = [Player("Player 1"), Player("Player 2"), Player("Player 3")]

    game = PokerGame(players)
    game.start_hand()

    PokerUI(game).run()


if __name__ == "__main__":
    main()
