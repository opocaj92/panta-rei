import math
import pygame

from game.core.scene import Scene
from game.rendering.renderer import PrototypeRenderer


class Scene11(Scene):
    """Marco looks at Stella, then deliberately follows her instruction to look up."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = PrototypeRenderer()
        self.phase = "dialogue"
        self.gaze_progress = 0.0
        self.phase_timer = 0.0
        self.speaking_time = 0.0
        self.transition_started = False

    def enter(self):
        self.phase = "dialogue"
        self.gaze_progress = 0.0
        self.phase_timer = 0.0
        self.speaking_time = 0.0
        self.transition_started = False
        self.game.dialogue.load("scene_11")

    def handle_input(self, event):
        # Intentionally accept no input until the dialogue has *already* ended.
        # KEYDOWNs (and held keys) from the speaking phase are therefore discarded,
        # so the player must make a fresh deliberate press afterwards.
        if self.phase != "waiting_for_look" or event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self.phase = "looking_up"
            self.phase_timer = 0.0

    def update(self, dt):
        if self.phase == "dialogue":
            self.speaking_time += dt
            self.game.dialogue.update(dt)
            if self.game.dialogue.finished:
                self.phase = "waiting_for_look"
            return

        if self.phase == "waiting_for_look":
            return

        if self.phase == "looking_up":
            duration = max(float(self.config.get("gaze_move_duration", 1.15)), 0.001)
            self.phase_timer += dt
            self.gaze_progress = min(1.0, self.phase_timer / duration)
            if self.gaze_progress >= 1.0:
                self.phase = "sky_hold"
                self.phase_timer = 0.0
            return

        if self.phase == "sky_hold":
            self.phase_timer += dt
            if self.phase_timer >= float(self.config.get("sky_hold_duration", 2.2)):
                self.phase = "fading_out"
                self.phase_timer = 0.0
                if not self.transition_started:
                    self.transition_started = True
                    transition = self.config.get("transition_out", {})
                    self.game.transitions.fade_to_black(
                        float(transition.get("duration", 1.15)),
                        on_complete=self._begin_black_hold,
                    )
            return

        if self.phase == "black_hold":
            self.phase_timer += dt
            if self.phase_timer >= float(self.config.get("black_hold_duration", 1.0)):
                self.game.scenes.change_scene(self.config.get("next_scene", "scene_12"))
                self.phase = "done"

    def _begin_black_hold(self):
        # Keep TransitionManager's fully black overlay in place while we wait.
        self.phase = "black_hold"
        self.phase_timer = 0.0

    @staticmethod
    def _smoothstep(value):
        value = max(0.0, min(1.0, value))
        return value * value * (3.0 - 2.0 * value)

    def render(self, screen):
        progress = self._smoothstep(self.gaze_progress)
        self.renderer.scene11_stella_to_sky(
            screen,
            gaze_progress=progress,
            speaking=(self.phase == "dialogue" and not self.game.dialogue.finished),
            speaking_time=self.speaking_time,
        )

        if self.phase == "dialogue":
            self.game.text_renderer.dialogue(screen, self.game.dialogue)
