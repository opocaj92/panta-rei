import math
import pygame


class RiverSeaRenderer:
    """Prototype visual for Scene 10: a deformable river joining an irreversible sea."""

    def render(self, screen, mouth_x, mouth_y, connected, elapsed):
        w, h = screen.get_size()
        screen.fill((17, 24, 36))

        # Sea: broad body on the left, with a gently moving boundary.
        sea_edge = int(w * 0.30)
        sea = pygame.Surface((sea_edge + 45, h), pygame.SRCALPHA)
        sea.fill((38, 91, 137, 255))
        screen.blit(sea, (0, 0))
        for y in range(25, h, 34):
            x2 = sea_edge - 15 + int(7 * math.sin(elapsed * 1.4 + y * 0.025))
            pygame.draw.line(screen, (79, 128, 163), (20, y), (x2, y), 2)

        # A quiet shoreline/boundary makes the target readable without UI text.
        shore_x = sea_edge + 4
        pygame.draw.line(screen, (113, 104, 88), (shore_x, 0), (shore_x, h), 5)

        # River is a thick Bezier-like polyline whose mouth is controlled by the player.
        source = pygame.Vector2(w - 40, h * 0.46)
        mouth = pygame.Vector2(mouth_x, mouth_y)
        c1 = pygame.Vector2(w * 0.78, h * 0.39)
        c2 = pygame.Vector2(max(mouth.x + 95, w * 0.48), h * 0.60)
        points = []
        for i in range(41):
            t = i / 40.0
            omt = 1.0 - t
            p = omt**3 * source + 3 * omt**2 * t * c1 + 3 * omt * t**2 * c2 + t**3 * mouth
            points.append((int(p.x), int(p.y)))

        # Dark banks underneath, then water. This keeps the former river legible after joining.
        pygame.draw.lines(screen, (84, 77, 65), False, points, 64)
        pygame.draw.lines(screen, (48, 107, 151), False, points, 52)
        pygame.draw.lines(screen, (94, 148, 181), False, points, 3)

        if connected:
            # Small blended mouth: continuous water, but the river course remains visible.
            pygame.draw.circle(screen, (43, 99, 145), (int(mouth.x), int(mouth.y)), 31)
            pygame.draw.circle(screen, (63, 119, 158), (int(mouth.x - 10), int(mouth.y)), 20)
