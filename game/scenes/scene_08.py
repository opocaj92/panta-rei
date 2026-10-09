import pygame

from game.core.scene import Scene
from game.core.timing import CompletionTimer
from game.rendering.stella_pov_renderer import StellaPOVRenderer


class Scene08(Scene):
    """Stella can optionally lean closer to Marco while speaking."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = StellaPOVRenderer(config, game.assets)
        self.camera_y = 0.0
        self.elapsed = 0.0
        self.approach = 0.0
        self.display_approach = 0.0
        self.dragging = False
        self.last_mouse_y = 0
        self.completion_timer = CompletionTimer()

    def help_needed(self):
        return not self.transition_started

    def enter(self):
        # Preserve the exact camera position passed by Scene 07.
        self.camera_y = float(self.incoming_state.get("camera_y", 0.0))
        self.approach = 0.0
        self.display_approach = 0.0
        self.dragging = False
        self.completion_timer.reset()
        self.game.dialogue.load("scene_08")

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
            self.mark_help_progress()
            self.last_mouse_y = event.pos[1]
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.mark_help_progress()
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # One-way approach: downward dragging never reverses progress.
            dy = max(0, self.last_mouse_y - event.pos[1])
            self.last_mouse_y = event.pos[1]
            sensitivity = float(self.config.get("approach", {}).get("drag_sensitivity", 0.0028))
            if dy > 0 and not self.transition_started:
                self.approach = min(1.0, self.approach + dy * sensitivity)
                self.mark_help_progress()

    def update(self, dt):
        self.elapsed += dt
        # Smooth visual movement without changing the drag's one-way progress.
        blend = 1.0 - pow(0.001, max(0.0, dt) / 0.22)
        self.display_approach += (self.approach - self.display_approach) * blend
        self.game.dialogue.update(dt)

        elapsed = self.completion_timer.update(dt, active=self.game.dialogue.finished)
        if not self.game.dialogue.finished:
            return
        delay = float(self.config.get("post_dialogue_delay", 1.0))
        if elapsed >= delay and not self.transition_started:
            self.request_transition(self.config.get("next_scene", "scene_09"), state={"camera_y": self.camera_y, "approach": self.approach})

    def render(self, screen):
        approach_cfg = self.config.get("approach", {})
        max_zoom = float(approach_cfg.get("max_safe_zoom", 1.38))
        zoom = 1.0 + (max_zoom - 1.0) * self.display_approach
        self.renderer.render(screen, self.camera_y, self.elapsed, zoom=zoom,
                             animate_phone=False, focus=(110, 285))

        self.render_dialogue_or_thought(
            screen, dialogue_rect=pygame.Rect(51, 273, screen.get_width() - 102, 66)
        )
