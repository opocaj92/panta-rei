import math
import pygame


class LoveSilhouetteRenderer:
    """Abstract prototype visual for Scene 09's joining/separating metaphor."""

    def render(self, screen, separation, phase, elapsed):
        w, h = screen.get_size()
        screen.fill((31, 18, 40))

        # Soft abstract background: nested hearts/ripples and drifting motes.
        center = (w // 2, h // 2 - 20)
        for i in range(5, 0, -1):
            radius = 55 + i * 42 + int(4 * math.sin(elapsed * 1.3 + i))
            color = (54 + i * 5, 31 + i * 4, 61 + i * 6)
            pygame.draw.circle(screen, color, center, radius, width=2)
        for i in range(18):
            x = int((i * 97 + elapsed * (8 + i % 3)) % (w + 60) - 30)
            y = 70 + (i * 61) % max(100, h - 150)
            pygame.draw.circle(screen, (116, 82, 121), (x, y), 2)

        half_span = int(separation)
        boy_x = w // 2 - half_span
        girl_x = w // 2 + half_span
        y = h // 2 + 25

        pulse = 1.0
        if phase == "joined":
            pulse = 1.0 + 0.055 * math.sin(elapsed * 8.0)

        self._draw_person(screen, boy_x, y, (77, 132, 196), pulse)
        self._draw_person(screen, girl_x, y, (214, 104, 157), pulse)

    def _draw_person(self, screen, x, y, color, scale):
        head_r = int(30 * scale)
        body_w = int(66 * scale)
        body_h = int(150 * scale)
        pygame.draw.circle(screen, color, (x, y - int(105 * scale)), head_r)
        body = pygame.Rect(0, 0, body_w, body_h)
        body.midtop = (x, y - int(72 * scale))
        pygame.draw.ellipse(screen, color, body)
