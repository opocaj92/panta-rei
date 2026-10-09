import pygame

from game.core.scene import Scene
from game.rendering.opening_sky_renderer import OpeningSkyRenderer


class Scene01(Scene):
    """Opening establishing shot with the game title."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = OpeningSkyRenderer(self.game.assets)
        self.elapsed = 0.0
        self.title_alpha = 0.0
        self.title_state = "WAITING"
        self.title_hold_timer = 0.0

    def enter(self):
        self.elapsed = 0.0
        self.title_alpha = 0.0
        self.title_state = "WAITING"
        self.title_hold_timer = 0.0
        self.renderer.reset()

    def update(self, dt):
        self.renderer.update(dt)
        self.elapsed += dt
        title = self.config.get("title", {})
        delay = float(title.get("delay", 2.0))
        fade_in = float(title.get("fade_in", 0.5))
        hold = float(title.get("hold", 2.5))
        fade_out = float(title.get("fade_out", 0.8))

        if self.title_state == "WAITING":
            if self.elapsed >= delay:
                self.title_state = "FADING_IN"
        elif self.title_state == "FADING_IN":
            self.title_alpha += (255.0 / max(fade_in, 0.001)) * dt
            if self.title_alpha >= 255.0:
                self.title_alpha = 255.0
                self.title_state = "HOLDING"
                self.title_hold_timer = 0.0
        elif self.title_state == "HOLDING":
            self.title_hold_timer += dt
            if self.title_hold_timer >= hold:
                self.title_state = "FADING_OUT"
        elif self.title_state == "FADING_OUT":
            self.title_alpha -= (255.0 / max(fade_out, 0.001)) * dt
            if self.title_alpha <= 0.0:
                self.title_alpha = 0.0
                self.title_state = "FINISHED"

        auto_delay = float(self.config.get("auto_delay", 7.0))
        if self.elapsed >= auto_delay and not self.transition_started:
            self.request_transition("scene_02")

    def render(self, screen):
        self.renderer.render(screen, title_alpha=self.title_alpha)
