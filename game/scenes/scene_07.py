import pygame

from game.core.scene import Scene
from game.rendering.stella_pov_renderer import StellaPOVRenderer


class Scene07(Scene):
    """Stella's POV: look up from her phone to Marco, then hear her reply."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = StellaPOVRenderer(config, game.assets)
        self.camera_y = 0.0
        self.start_y = 0.0
        self.target_y = 0.0
        self.pan_elapsed = 0.0
        self.pan_duration = 1.0
        self.pan_started = False
        self.pan_complete = False
        self.dialogue_started = False
        self.elapsed = 0.0

    def allows_dialogue_advance(self):
        return self.dialogue_started and not self.transition_started

    def help_needed(self):
        return not self.pan_started

    def enter(self):
        camera = self.config.get("camera", {})
        self.start_y = float(camera.get("phone_y", 360.0))
        self.target_y = float(camera.get("marco_y", 0.0))
        self.pan_duration = max(0.001, float(camera.get("pan_duration", 1.25)))
        self.camera_y = self.start_y
        self.game.dialogue.load("scene_07")

    def handle_input(self, event):
        if self.pan_started or event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            self.pan_started = True

            self.pan_elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

        if not self.pan_started:
            return

        if not self.pan_complete:
            self.pan_elapsed += dt
            t = min(1.0, self.pan_elapsed / self.pan_duration)
            # Smoothstep: gentle acceleration/deceleration, still deterministic.
            smooth_t = t * t * (3.0 - 2.0 * t)
            self.camera_y = self.start_y + (self.target_y - self.start_y) * smooth_t

            if t >= 1.0:
                self.camera_y = self.target_y
                self.pan_complete = True
                self.dialogue_started = True
            return

        self.game.dialogue.update(dt)

        if self.game.dialogue.finished and not self.transition_started:
            self.request_transition(self.config.get("next_scene", "scene_08"), state={"camera_y": self.camera_y})

    def render(self, screen):
        self.renderer.render(screen, self.camera_y, self.elapsed, animate_phone=not self.pan_complete)

        if self.dialogue_started:
            self.game.text_renderer.dialogue(screen, self.game.dialogue)
