import pygame

from game.card import Card
from game.game import PokerGame


class PokerUI:
    def __init__(self, game: PokerGame) -> None:
        self.game = game

        pygame.init()
        self.screen = pygame.display.set_mode((1024, 650))
        pygame.display.set_caption("Poker - Texas Hold'em")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("arial", 22)
        self.card_font = pygame.font.SysFont("arial", 26, bold=True)

    def draw_text(self, text: str, x: int, y: int, color: str = "white") -> None:
        image = self.font.render(text, True, color)
        self.screen.blit(image, (x, y))

    def draw_card(self, card: Card | None, x: int, y: int) -> None:
        rect = pygame.Rect(x, y, 52, 72)

        pygame.draw.rect(
            self.screen, "white" if card else "#29584a", rect, border_radius=6
        )
        pygame.draw.rect(self.screen, "#17382e", rect, 2, border_radius=6)

        if card is not None:
            ranks = {11: "J", 12: "Q", 13: "K", 14: "A"}
            symbol = card.suit[0]
            label = f"{ranks.get(card.rank, str(card.rank))}{symbol}"

            color = "#b32222" if symbol in ("H", "D") else "#111111"
            image = self.card_font.render(label, True, color)

            self.screen.blit(image, image.get_rect(center=rect.center))

    def draw(self) -> None:
        self.screen.fill("#152522")

        # Table
        pygame.draw.ellipse(self.screen, "#236346", (72, 145, 880, 355))
        pygame.draw.ellipse(self.screen, "#b39c6a", (72, 145, 880, 355), 5)

        # Community cards
        self.draw_text(f"Phase: {self.game.phase.name}", 415, 25)
        self.draw_text("Cartes communes", 420, 245)

        for index in range(5):
            card = (
                self.game.community_cards[index]
                if index < len(self.game.community_cards)
                else None
            )
            self.draw_card(card, 347 + index * 66, 290)

        # Players
        positions = [(80, 22), (744, 22), (430, 505)]

        for index, player in enumerate(self.game.players):
            x, y = positions[index]
            dealer = " (D)" if index == self.game.dealer_index else ""

            self.draw_text(f"{player.name}{dealer} - {player.stack} jetons", x, y)

            for card_index, card in enumerate(player.hand):
                self.draw_card(card, x + card_index * 62, y + 32)

        self.draw_text(
            "ESPACE: phase suivante / nouvelle main  |  ECHAP: quitter", 90, 619
        )

    def run(self) -> None:
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.game.advance_phase()

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
