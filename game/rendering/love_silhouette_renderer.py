"""Scene 09: two independent pixel-art sprites meet at their lip anchors."""
import pygame


class LoveSilhouetteRenderer:
    def __init__(self, assets):
        self.background = assets.image("scene_09/cosmic_background", "scene_09/cosmic_background.png", alpha=False, required=True)
        self.boy = assets.image("scene_09/marco_silhouette", "scene_09/marco_silhouette.png", alpha=True, required=True)
        self.girl = assets.image("scene_09/stella_silhouette", "scene_09/stella_silhouette.png", alpha=True, required=True)
        # Mouth-edge anchors, measured on opaque pixels (not mouth centres).
        # The y coordinates also account for Stella's seven pixels of transparent
        # padding below her visible feet, so both figures stand on the window edge.
        self.boy_lip = (199, 96)
        self.girl_lip = (70, 89)
        self.boy_bottom = self.boy.get_bounding_rect(min_alpha=30).bottom
        self.girl_bottom = self.girl.get_bounding_rect(min_alpha=30).bottom
        self._scaled_backgrounds = {}

    def anchors(self, screen, separation):
        cx = screen.get_width() // 2
        # At zero separation, the rightmost lip pixel of Marco meets the
        # leftmost lip pixel of Stella; do not align their mouth centres.
        return cx - separation, cx + separation

    def rects(self, screen, separation):
        left_x, right_x = self.anchors(screen, separation)
        # Place the actual visible bottom edge, not the transparent PNG canvas,
        # on the last row of the viewport.
        boy_y = screen.get_height() - self.boy_bottom
        girl_y = screen.get_height() - self.girl_bottom
        return (pygame.Rect(round(left_x - self.boy_lip[0]), boy_y, *self.boy.get_size()),
                pygame.Rect(round(right_x - self.girl_lip[0] + 1), girl_y, *self.girl.get_size()))

    def side_at(self, screen, pos, separation):
        boy, girl = self.rects(screen, separation)
        # Test visible alpha rather than a centre-distance circle.
        for side, rect, sprite in (("left", boy, self.boy), ("right", girl, self.girl)):
            if rect.collidepoint(pos):
                x, y = pos[0] - rect.left, pos[1] - rect.top
                if sprite.get_at((x, y)).a > 30:
                    return side
        return None

    def render(self, screen, separation, phase, elapsed):
        size = screen.get_size()
        if size == self.background.get_size():
            bg = self.background
        else:
            if size not in self._scaled_backgrounds:
                self._scaled_backgrounds[size] = pygame.transform.scale(self.background, size)
            bg = self._scaled_backgrounds[size]
        screen.blit(bg, (0, 0))
        boy, girl = self.rects(screen, separation)
        screen.blit(self.boy, boy.topleft)
        screen.blit(self.girl, girl.topleft)
