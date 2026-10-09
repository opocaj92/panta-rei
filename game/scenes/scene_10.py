import pygame

from game.core.scene import Scene
from game.core.timing import CompletionTimer
from game.rendering.river_sea_renderer import RiverSeaRenderer


class Scene10(Scene):
    """Pull the visible river leftward until it irreversibly joins the sea."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = None
        self.elapsed = 0.0
        self.dragging = False
        self.connected = False
        self.completion_timer = CompletionTimer()
        self.leading_x = 0.0
        self.drag_offset = 0.0

    @property
    def interaction_cfg(self):
        return self.config.get('interaction', {})

    def help_needed(self):
        return not self.dragging and not self.connected and not self.transition_started

    def enter(self):
        self.game.dialogue.load('scene_10')
        self.renderer = RiverSeaRenderer(self.game.assets)
        self.mark_help_progress()
        w, _ = self.game.screen.get_size()
        self.leading_x = w * float(self.interaction_cfg.get('initial_visible_fraction', 0.05))
        self.leading_x = w - self.leading_x

    def handle_input(self, event):
        if self.connected:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            w, h = self.game.screen.get_size()
            # Grab the river's visible tip, not arbitrary landscape pixels.
            radius = float(self.interaction_cfg.get('grab_radius', 35.0))
            center_y = h * float(self.interaction_cfg.get('river_center_fraction', 0.50))
            if abs(x - self.leading_x) <= radius and abs(y - center_y) <= h * 0.11:
                self.dragging = True
                self.mark_help_progress()
                self.drag_offset = self.leading_x - x
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.mark_help_progress()
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            w, _ = self.game.screen.get_size()
            previous = self.leading_x
            self.leading_x = max(0.0, min(w * 0.95, event.pos[0] + self.drag_offset))
            if self.leading_x != previous:
                self.mark_help_progress()
            if self.leading_x <= w * float(self.interaction_cfg.get('sea_edge_fraction', 0.31)):
                self.leading_x = 0.0
                self.connected = True
                self.dragging = False

    def update(self, dt):
        self.elapsed += dt
        self.game.dialogue.update(dt)
        if self.connected and self.game.dialogue.finished:
            elapsed = self.completion_timer.update(dt, active=True)
            delay = float(self.config.get('post_complete_delay', 0.55))
            if elapsed >= delay and not self.transition_started:
                self.request_transition(self.config.get('next_scene', 'scene_11'))
        else:
            self.completion_timer.reset()

    def render(self, screen):
        self.renderer.render(screen, self.leading_x, self.connected, self.elapsed)
        self.game.text_renderer.dialogue(screen, self.game.dialogue)
