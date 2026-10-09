import pygame

from game.core.scene import Scene
from game.core.timing import CompletionTimer
from game.rendering.river_sea_renderer import RiverSeaRenderer
from game.systems.river_drag import RiverDragSystem


class Scene10(Scene):
    """Pull the visible river leftward until it irreversibly joins the sea."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = None
        self.elapsed = 0.0
        self.river_drag = None
        self.completion_timer = CompletionTimer()

    @property
    def interaction_cfg(self):
        return self.config.get('interaction', {})

    def help_needed(self):
        return not self.river_drag.connected and not self.transition_started

    def enter(self):
        self.game.dialogue.load('scene_10')
        self.renderer = RiverSeaRenderer(self.game.assets)

        self.river_drag = RiverDragSystem(self.interaction_cfg, self.game.screen.get_size())

    def handle_input(self, event):
        self.river_drag.handle_event(event)

    def update(self, dt):
        self.elapsed += dt
        self.game.dialogue.update(dt)
        if self.river_drag.connected and self.game.dialogue.finished:
            elapsed = self.completion_timer.update(dt, active=True)
            delay = float(self.config.get('post_complete_delay', 0.55))
            if elapsed >= delay and not self.transition_started:
                self.request_transition(self.config.get('next_scene', 'scene_11'))
        else:
            self.completion_timer.reset()

    def render(self, screen):
        self.renderer.render(screen, self.river_drag.leading_x, self.river_drag.connected, self.elapsed)
        self.game.text_renderer.dialogue(screen, self.game.dialogue)
