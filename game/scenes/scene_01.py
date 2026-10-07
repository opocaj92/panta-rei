import pygame

from game.core.scene import Scene
from game.rendering.renderer import PrototypeRenderer


class Scene01(Scene):
    """Opening establishing shot with the game title."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = PrototypeRenderer()
        self.elapsed = 0.0
        self.title_alpha = 0.0
        self.title_state = "WAITING"
        self.title_hold_timer = 0.0
        self.transition_started = False
        self.title_font = self.game.assets.font("title", size=96)

    def enter(self):
        self.elapsed = 0.0
        self.title_alpha = 0.0
        self.title_state = "WAITING"
        self.title_hold_timer = 0.0
        self.transition_started = False

    def update(self, dt):
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
            self.transition_started = True
            self.game.scenes.change_scene(
                "scene_02",
                transition_config=self.config.get("transition_out"),
            )

    def render(self, screen):
        self.renderer.background(screen, self.config.get("background", "lake"))

        if self.title_alpha > 0:
            title_surface = self.title_font.render(
                self.config.get("title", {}).get("text", "Panta Rei"),
                True,
                (245, 245, 245),
            )
            title_surface.set_alpha(int(self.title_alpha))
            title_rect = title_surface.get_rect(
                center=(screen.get_width() // 2, screen.get_height() // 2)
            )
            screen.blit(title_surface, title_rect)
