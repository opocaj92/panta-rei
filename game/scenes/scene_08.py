import pygame

from game.core.scene import Scene
from game.core.timing import CompletionTimer
from game.rendering.stella_pov_renderer import StellaPOVRenderer
from game.systems.approach import ApproachSystem


class Scene08(Scene):
    """Stella can optionally lean closer to Marco while speaking."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = StellaPOVRenderer(config, game.assets)
        self.camera_y = 0.0
        self.elapsed = 0.0
        self.approach_system = ApproachSystem(config.get("approach", {}).get("drag_sensitivity", 0.0028))
        self.completion_timer = CompletionTimer()

    def help_needed(self):
        return not self.transition_started and self.approach_system.progress < 1.0

    def enter(self):
        # Preserve the exact camera position passed by Scene 07.
        self.camera_y = float(self.incoming_state.get("camera_y", 0.0))
        self.approach_system.reset()
        self.completion_timer.reset()
        self.game.dialogue.load("scene_08")

    def handle_input(self, event):
        self.approach_system.handle_event(event, enabled=not self.transition_started)

    def update(self, dt):
        self.elapsed += dt
        self.approach_system.update(dt)
        self.game.dialogue.update(dt)

        elapsed = self.completion_timer.update(dt, active=self.game.dialogue.finished)
        if not self.game.dialogue.finished:
            return
        delay = float(self.config.get("post_dialogue_delay", 1.0))
        if elapsed >= delay and not self.transition_started:
            self.request_transition(self.config.get("next_scene", "scene_09"), state={"camera_y": self.camera_y, "approach": self.approach_system.progress})

    def render(self, screen):
        approach_cfg = self.config.get("approach", {})
        max_zoom = float(approach_cfg.get("max_safe_zoom", 1.38))
        zoom = 1.0 + (max_zoom - 1.0) * self.approach_system.display_progress
        self.renderer.render(screen, self.camera_y, self.elapsed, zoom=zoom,
                             animate_phone=False, focus=(110, 285))

        self.render_dialogue_or_thought(
            screen, dialogue_rect=pygame.Rect(51, 273, screen.get_width() - 102, 66)
        )
