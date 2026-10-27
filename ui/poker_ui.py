import pygame

from game.betting import Action
from game.card import Card
from game.game import Phase, PokerGame


class PokerUI:
    def __init__(self, game: PokerGame) -> None:
        self.game = game

        pygame.init()
        self.screen = pygame.display.set_mode((1100, 770))
        pygame.display.set_caption("Poker Texas Hold'em - 3 joueurs")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("arial", 22)
        self.small_font = pygame.font.SysFont("arial", 18)
        self.card_font = pygame.font.SysFont("arial", 26, bold=True)

        self.raise_to = self.game.minimum_raise_to()
        self.message = "Choisis une action pour le joueur indiqué."

    def text(
        self, value: str, x: int, y: int, color: str = "white", small: bool = False
    ) -> None:
        font = self.small_font if small else self.font
        image = font.render(value, True, color)
        self.screen.blit(image, (x, y))

    def card(self, card: Card | None, x: int, y: int) -> None:
        rect = pygame.Rect(x, y, 54, 75)

        pygame.draw.rect(
            self.screen, "white" if card else "#2e6051", rect, border_radius=6
        )
        pygame.draw.rect(self.screen, "#16382e", rect, 2, border_radius=6)

        if card is not None:
            rank = {11: "J", 12: "Q", 13: "K", 14: "A"}.get(card.rank, str(card.rank))
            symbol = card.suit[0]
            color = "#bb2727" if symbol in ("H", "D") else "#111111"

            label = self.card_font.render(rank + symbol, True, color)
            self.screen.blit(label, label.get_rect(center=rect.center))

    def act(self, action: Action) -> None:
        if action not in self.game.get_legal_actions():
            self.message = f"Action impossible : {action.value}"
            return

        try:
            if action == Action.RAISE:
                self.game.apply_action(action, self.raise_to)
            else:
                self.game.apply_action(action)

            self.message = f"Dernière action : {action.value}"
            self.raise_to = self.game.minimum_raise_to()
        except ValueError as error:
            self.message = str(error)

    def handle_key(self, key: int) -> None:
        if self.game.phase == Phase.SHOWDOWN:
            winner_keys = {
                pygame.K_1: 0,
                pygame.K_KP1: 1,
                pygame.K_2: 1,
                pygame.K_KP2: 1,
                pygame.K_3: 2,
                pygame.K_KP3: 2,
            }

            if key in winner_keys:
                try:
                    self.game.award_showdown(winner_keys[key])
                    self.message = "Pot attribué au gagnant."
                except ValueError as error:
                    self.message = str(error)
            return

        if self.game.phase == Phase.FINISHED:
            if key == pygame.K_n:
                try:
                    self.game.start_hand()
                    self.raise_to = self.game.minimum_raise_to()
                    self.message = "Nouvelle main."
                except ValueError as error:
                    self.message = str(error)
            return

        if key == pygame.K_f:
            self.act(Action.FOLD)

        elif key == pygame.K_c:
            action = Action.CHECK if self.game.amount_to_call() == 0 else Action.CALL
            self.act(action)

        elif key == pygame.K_r:
            self.act(Action.RAISE)

        elif (
            key in (pygame.K_UP, pygame.K_DOWN)
            and Action.RAISE in self.game.get_legal_actions()
        ):
            step = 20 if key == pygame.K_UP else -20

            self.raise_to = max(
                self.game.minimum_raise_to(),
                min(self.raise_to + step, self.game.maximum_raise_to()),
            )

    def draw(self) -> None:
        self.screen.fill("#142520")

        # Table
        pygame.draw.ellipse(self.screen, "#205c42", (90, 110, 920, 400))
        pygame.draw.ellipse(self.screen, "#bea36b", (90, 110, 920, 400), 5)

        # Community cards
        self.text(f"Phase: {self.game.phase.name}", 440, 15)
        self.text(
            f"Pot : {self.game.pot} | Plus haute mise : {self.game.betting.highest_bet}",
            320,
            200,
        )

        for index in range(5):
            card = (
                self.game.community_cards[index]
                if index < len(self.game.community_cards)
                else None
            )
            self.card(card, 390 + index * 64, 265)

        # Players
        positions = [(90, 15), (785, 15), (425, 500)]

        sb = (self.game.dealer_index + 1) % 3

        for index, player in enumerate(self.game.players):
            x, y = positions[index]

            role = (
                "D"
                if index == self.game.dealer_index
                else "SB"
                if index == sb
                else "BB"
            )

            marker = " <--- À JOUER" if index == self.game.current_player_index else ""

            self.text(f"{player.name} ({role}){marker}", x, y)
            self.text(
                f"Jetons : {player.stack} | Mise : {player.current_bet}",
                x,
                y + 29,
                small=True,
            )

            if player.folded:
                self.text("FOLD", x, y + 53, color="#ff9e9e")

            for card_index, card in enumerate(player.hand):
                self.card(card, x + card_index * 64, y + 60)

        if self.game.current_player_index is not None:
            actions = self.game.get_legal_actions()
            legal = ", ".join(sorted(action.value for action in actions))

            self.text(
                f"Actions : {legal} | À suivre : {self.game.amount_to_call()}",
                70,
                640,
                small=True,
            )

            if Action.RAISE in actions:
                self.text(
                    f"Relancer à : {self.raise_to} (min {self.game.minimum_raise_to()}, max {self.game.maximum_raise_to()})",
                    70,
                    665,
                    small=True,
                )

            self.text(
                "F: fold | C : check/call | R : raise | Flèches haut/bas : ajuster montant",
                70,
                690,
                small=True,
            )

        elif self.game.phase == Phase.FINISHED:
            if self.game.winner_index is not None:
                winner = self.game.players[self.game.winner_index].name
                self.text(
                    f"Gagnant : {winner} | N : nouvelle main", 70, 665, small=True
                )

        self.text(self.message[:100], 70, 725, "#c6e1bc", small=True)

    def run(self) -> None:
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        self.handle_key(event.key)

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
