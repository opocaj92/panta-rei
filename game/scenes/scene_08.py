import pygame

from game.core.scene import Scene
from game.rendering.stella_pov_renderer import StellaPOVRenderer


class Scene08(Scene):
    """Stella can optionally lean closer to Marco while speaking."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = StellaPOVRenderer()
        self.camera_y = 0.0
        self.elapsed = 0.0
        self.approach = 0.0
        self.dragging = False
        self.last_mouse_y = 0
        self.post_dialogue_elapsed = 0.0
        self.transition_started = False

    def enter(self):
        self.camera_y = float(self.incoming_state.get("camera_y", 0.0))
        self.game.dialogue.load("scene_08")

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
            self.last_mouse_y = event.pos[1]
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Stella may move closer to Marco, but never farther away again.
            dy = self.last_mouse_y - event.pos[1]
            self.last_mouse_y = event.pos[1]
            if dy > 0:
                sensitivity = float(
                    self.config.get("approach", {}).get("drag_sensitivity", 0.004)
                )
                self.approach = min(1.0, self.approach + dy * sensitivity)

    def update(self, dt):
        self.elapsed += dt
        self.game.dialogue.update(dt)

        if not self.game.dialogue.finished:
            self.post_dialogue_elapsed = 0.0
            return

        self.post_dialogue_elapsed += dt
        delay = float(self.config.get("post_dialogue_delay", 1.0))
        if self.post_dialogue_elapsed >= delay and not self.transition_started:
            self.transition_started = True
            self.game.scenes.change_scene(
                self.config.get("next_scene", "scene_09"),
                transition_config=self.config.get("transition_out"),
                state={"camera_y": self.camera_y, "approach": self.approach},
            )

    def render(self, screen):
        approach_cfg = self.config.get("approach", {})
        max_zoom = float(approach_cfg.get("max_safe_zoom", 1.28))
        zoom = 1.0 + (max_zoom - 1.0) * self.approach
        self.renderer.render(screen, self.camera_y, self.elapsed, zoom=zoom)

        line = self.game.dialogue.current_line
        if line and line.get("type") == "thought":
            self.game.text_renderer.thought(screen, self.game.dialogue)
        else:
            self.game.text_renderer.dialogue(screen, self.game.dialogue)
