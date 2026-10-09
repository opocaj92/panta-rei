import math
import pygame

class PrototypeRenderer:
    """
    Temporary placeholder renderer.

    It will eventually be replaced by the illustrated assets without
    changing scene logic.
    """

    def __init__(self):
        self.title_font = pygame.font.Font(None, 36)

    def background(self, screen, kind):
        legacy = pygame.Surface((1000, 600))
        self._background_legacy(legacy, kind)
        screen.blit(pygame.transform.scale(legacy, screen.get_size()), (0, 0))

    def _background_legacy(self, screen, kind):
        if kind == "lake_establishing":
            kind = "lake"

        width, height = screen.get_size()
        screen.fill((13, 22, 35))

        if kind in {"lake", "stella", "river", "grass", "city", "sky"}:
            self._stars(screen)
            pygame.draw.circle(screen, (235, 235, 205), (width // 2, 100), 38)

        if kind == "lake":
            pygame.draw.rect(screen, (18, 40, 54), (0, 330, width, 270))
            pygame.draw.circle(screen, (55, 55, 65), (455, 390), 28)
            pygame.draw.circle(screen, (65, 60, 75), (545, 390), 28)
            pygame.draw.rect(screen, (55, 55, 65), (425, 415, 60, 85))
            pygame.draw.rect(screen, (65, 60, 75), (515, 415, 60, 85))

        elif kind == "stella":
            self._stella(screen)

        elif kind == "river":
            # Marco's literal seated POV from the river bank: a low, oblique
            # view across the water, not a map-like/aerial representation.
            horizon_y = int(height * 0.42)

            # Far bank, kept low enough that the water occupies the visual field.
            pygame.draw.polygon(
                screen, (24, 43, 39),
                [(0, horizon_y + 20), (0, horizon_y - 5),
                 (180, horizon_y - 18), (350, horizon_y + 2),
                 (540, horizon_y - 12), (730, horizon_y + 5),
                 (width, horizon_y - 14), (width, horizon_y + 28)]
            )

            # Water recedes toward the far bank and fills the middle foreground.
            pygame.draw.polygon(
                screen, (27, 67, 84),
                [(0, horizon_y + 18), (width, horizon_y + 25),
                 (width, height), (0, height)]
            )

            # Horizontal moonlight/current marks reinforce looking ACROSS the river.
            for row, span in enumerate(range(70, 390, 42)):
                y = horizon_y + 45 + row * 34
                x = width // 2 - span // 2 + int(14 * math.sin(row * 1.7))
                pygame.draw.line(screen, (104, 139, 151), (x, y), (x + span, y + 2), 2)

            # Near bank intrudes into the bottom corners, placing Marco at its edge.
            pygame.draw.polygon(
                screen, (31, 54, 37),
                [(0, height), (0, height - 105), (155, height - 72),
                 (270, height), (0, height)]
            )
            pygame.draw.polygon(
                screen, (31, 54, 37),
                [(width, height), (width, height - 70),
                 (width - 115, height - 52), (width - 205, height), (width, height)]
            )
            for x in range(0, 180, 14):
                pygame.draw.line(screen, (48, 78, 48), (x, height),
                                 (x + 7, height - 45 - (x % 31)), 2)

        elif kind == "grass":
            for x in range(0, width, 8):
                top_y = 470 + int(12 * math.sin(x * 0.08))
                pygame.draw.line(screen, (45, 80, 50), (x, 500), (x + 3, top_y), 2)

        elif kind == "city":
            for x, h in [(60, 100), (170, 150), (290, 80), (420, 130),
                         (560, 110), (700, 175), (850, 95)]:
                pygame.draw.rect(screen, (25, 32, 45), (x, 430 - h, 80, h))
                for wx in range(x + 12, x + 70, 18):
                    for wy in range(440 - h, 420, 25):
                        pygame.draw.rect(screen, (180, 150, 70), (wx, wy, 5, 5))


    def scene11_stella_to_sky(self, screen, gaze_progress=0.0, speaking=False, speaking_time=0.0):
        """Scene 11 POV, authored in legacy prototype coordinates and scaled to 640x360."""
        target = screen
        screen = pygame.Surface((1000, 600))
        width, height = screen.get_size()
        p = max(0.0, min(1.0, float(gaze_progress)))

        # Reuse the same night-sky language as the opening scene.
        screen.fill((13, 22, 35))
        self._stars(screen)
        pygame.draw.circle(screen, (235, 235, 205), (width // 2, 100), 38)

        # At p=0 this matches the isolated Stella framing used in Scene 02.
        # Raising Marco's gaze moves Stella down and out rather than cross-fading her.
        offset_y = int(p * (height + 180))
        bob = int(2.0 * math.sin(speaking_time * 7.0)) if speaking else 0
        head_y = 300 + offset_y + bob
        body_y = 345 + offset_y + bob
        phone_y = 335 + offset_y + bob

        pygame.draw.circle(screen, (210, 170, 155), (500, head_y), 45)
        pygame.draw.rect(screen, (80, 65, 90), (445, body_y, 110, 145), border_radius=20)
        pygame.draw.rect(screen, (20, 20, 25), (530, phone_y, 45, 75), border_radius=5)
        pygame.draw.rect(screen, (100, 150, 190), (535, phone_y + 6, 35, 55), border_radius=2)

        # Minimal replaceable prototype speaking animation: mouth opens/closes and
        # Stella makes a tiny head/body motion. Final animation assets can replace it.
        if speaking and head_y < height + 60:
            mouth_open = 3 + int(3 * (0.5 + 0.5 * math.sin(speaking_time * 15.0)))
            pygame.draw.ellipse(screen, (105, 55, 58), (489, head_y + 13, 22, mouth_open))
        elif head_y < height + 60:
            pygame.draw.line(screen, (105, 55, 58), (490, head_y + 15), (510, head_y + 15), 2)

        target.blit(pygame.transform.scale(screen, target.get_size()), (0, 0))

    def _stella(self, screen):
        pygame.draw.circle(screen, (210, 170, 155), (500, 300), 45)
        pygame.draw.rect(screen, (80, 65, 90), (445, 345, 110, 145), border_radius=20)
        pygame.draw.rect(screen, (20, 20, 25), (530, 335, 45, 75), border_radius=5)
        pygame.draw.rect(screen, (100, 150, 190), (535, 341, 35, 55), border_radius=2)

    def _stars(self, screen):
        stars = [(70, 80), (130, 150), (210, 55), (290, 110), (380, 70),
                 (470, 160), (600, 55), (690, 130), (780, 80),
                 (900, 150), (950, 60), (550, 190)]
        for x, y in stars:
            pygame.draw.circle(screen, (220, 220, 210), (x, y), 2)

    def label(self, screen, text):
        surface = self.title_font.render(text, True, (230, 230, 230))
        screen.blit(surface, (screen.get_width() // 2 - surface.get_width() // 2, 25))
