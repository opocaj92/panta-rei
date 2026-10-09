"""Animated, masked two-background reveal for Scene 10."""
import pygame


class RiverSeaRenderer:
    FRAME_RATE = 5.0
    FRAME_COUNT = 8

    def __init__(self, assets):
        self.empty = [assets.image(f'scene_10/empty_{i:02}', f'scene_10/empty_{i:02}.png', alpha=False, required=True) for i in range(1, 9)]
        self.connected = [assets.image(f'scene_10/connected_{i:02}', f'scene_10/connected_{i:02}.png', alpha=False, required=True) for i in range(1, 9)]
        self.river = [assets.image(f'scene_10/river_overlay_{i:02}', f'scene_10/river_overlay_{i:02}.png', alpha=True, required=True) for i in range(1, 9)]
        self._scaled = {}

    def _frames(self, size):
        if size not in self._scaled:
            self._scaled[size] = tuple(
                [pygame.transform.smoothscale(frame, size) for frame in group]
                for group in (self.empty, self.connected, self.river)
            )
        return self._scaled[size]

    def render(self, screen, leading_x, connected, elapsed):
        width, height = screen.get_size()
        empty, full, overlay = self._frames((width, height))
        frame = int(elapsed * self.FRAME_RATE) % self.FRAME_COUNT
        if connected:
            screen.blit(full[frame], (0, 0))
            return
        screen.blit(empty[frame], (0, 0))
        start = max(0, min(width, round(leading_x)))
        if start < width:
            area = pygame.Rect(start, 0, width - start, height)
            screen.blit(overlay[frame], (start, 0), area)
