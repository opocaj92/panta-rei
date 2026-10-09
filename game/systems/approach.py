"""Reusable upward-drag progress with exponential visual smoothing."""
import pygame


class ApproachSystem:
    def __init__(self, sensitivity=0.0028, smoothing_time=0.22):
        self.sensitivity = float(sensitivity)
        self.smoothing_time = smoothing_time
        self.reset()

    def reset(self):
        self.progress = 0.0
        self.display_progress = 0.0
        self.dragging = False
        self.last_y = 0

    def handle_event(self, event, enabled=True):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
            self.last_y = event.pos[1]
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dy = max(0, self.last_y - event.pos[1])
            self.last_y = event.pos[1]
            if enabled:
                self.progress = min(1.0, self.progress + dy * self.sensitivity)

    def update(self, dt):
        blend = 1.0 - pow(0.001, max(0.0, dt) / self.smoothing_time)
        self.display_progress += (self.progress - self.display_progress) * blend
