"""Direction-constrained symmetric silhouette dragging."""
import pygame


class SilhouetteDragSystem:
    def __init__(self):
        self.dragging = False
        self.side = None
        self.last_x = 0

    def start(self, side, x):
        if side is not None:
            self.dragging = True
            self.side = side
            self.last_x = x

    def stop(self):
        self.dragging = False
        self.side = None

    def delta(self, event, sensitivity, approaching):
        if event.type != pygame.MOUSEMOTION or not self.dragging:
            return 0.0
        dx = event.pos[0] - self.last_x
        self.last_x = event.pos[0]
        radial = (-dx if self.side == 'left' else dx) * float(sensitivity)
        return min(0.0, radial) if approaching else max(0.0, radial)
