import pygame


class GazeSystem:
    """
    Reusable discrete gaze-input system.

    It translates directional input into a requested view. It does not own
    the scene's presentation state and does not render anything.
    """

    def __init__(self, views, sky_view=None, initial_view=None):
        if not views:
            raise ValueError("GazeSystem requires at least one horizontal view")

        self.views = list(views)
        self.sky_view = sky_view

        initial_view = initial_view or self.views[0]
        if initial_view not in self.views:
            raise ValueError(f"Initial gaze view must be horizontal: {initial_view}")

        self.index = self.views.index(initial_view)
        self.in_sky = False

    def set_horizontal_view(self, view):
        if view not in self.views:
            raise ValueError(f"Unknown horizontal gaze view: {view}")
        self.index = self.views.index(view)
        self.in_sky = False

    def handle_key(self, key):
        """Return the requested view, or None when the key changes nothing."""
        if key in (pygame.K_UP, pygame.K_w):
            if self.sky_view is not None:
                self.in_sky = True
                return self.sky_view
            return None

        if key in (pygame.K_DOWN, pygame.K_s):
            if self.in_sky:
                self.in_sky = False
                return self.views[self.index]
            return None

        if key in (pygame.K_RIGHT, pygame.K_d):
            self.index = (self.index + 1) % len(self.views)
            self.in_sky = False
            return self.views[self.index]

        if key in (pygame.K_LEFT, pygame.K_a):
            self.index = (self.index - 1) % len(self.views)
            self.in_sky = False
            return self.views[self.index]

        return None
