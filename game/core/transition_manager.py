import pygame


class TransitionManager:
    """Shared fade transition implementation."""

    def __init__(self):
        self.alpha = 0
        self.active = False
        self.duration = 1.0
        self.elapsed = 0.0
        self.start_alpha = 0
        self.end_alpha = 0
        self.on_complete = None
        self.blink_on_closed = None
        self.blink_opening = False
        self._overlay = None

    def clear(self):
        self.alpha = 0
        self.active = False
        self.elapsed = 0.0
        self.start_alpha = 0
        self.end_alpha = 0
        self.duration = 1.0
        self.on_complete = None
        self.blink_on_closed = None
        self.blink_opening = False

    def _start_fade(self, start_alpha, end_alpha, duration, on_complete=None):
        self.blink_on_closed = None
        self.blink_opening = False
        self.start_alpha = start_alpha
        self.end_alpha = end_alpha
        self.alpha = start_alpha
        self.duration = max(float(duration), 0.001)
        self.elapsed = 0.0
        self.active = True
        self.on_complete = on_complete

    def fade_to_black(self, duration=1.0, on_complete=None):
        self._start_fade(0, 255, duration, on_complete)

    def fade_from_black(self, duration=1.0, on_complete=None):
        self._start_fade(255, 0, duration, on_complete)

    def eye_blink(self, duration=1.2, on_closed=None):
        """Close to black, invoke the scene-swap callback, then reopen.

        The callback fires while the overlay is fully opaque so SceneManager can
        replace the active scene without exposing an intermediate frame.
        """
        half = max(float(duration) / 2.0, 0.001)

        def closed():
            callback = self.blink_on_closed
            self.blink_on_closed = None
            if callback:
                callback()
            # A callback may have initiated a different transition.
            if not self.active:
                self._start_fade(255, 0, half)
                self.blink_opening = True

        self._start_fade(0, 255, half, on_complete=closed)
        self.blink_on_closed = on_closed

    def update(self, dt):
        if not self.active:
            return

        self.elapsed += dt
        progress = min(1.0, self.elapsed / self.duration)
        self.alpha = int(
            self.start_alpha
            + (self.end_alpha - self.start_alpha) * progress
        )

        if progress >= 1.0:
            self.active = False
            self.alpha = self.end_alpha
            callback = self.on_complete
            self.on_complete = None
            if callback:
                callback()

    def render(self, screen):
        if self.alpha <= 0:
            return

        if self._overlay is None or self._overlay.get_size() != screen.get_size():
            self._overlay = pygame.Surface(screen.get_size())
            self._overlay.fill((0, 0, 0))
        self._overlay.set_alpha(self.alpha)
        screen.blit(self._overlay, (0, 0))
