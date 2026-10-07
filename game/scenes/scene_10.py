import pygame

from game.core.scene import Scene
from game.rendering.river_sea_renderer import RiverSeaRenderer


class Scene10(Scene):
    """The player irreversibly draws the river into the sea."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = RiverSeaRenderer()
        self.elapsed = 0.0
        self.dragging = False
        self.connected = False
        self.transition_started = False
        self.post_complete_elapsed = 0.0
        self.mouth = pygame.Vector2(0, 0)

    @property
    def interaction_cfg(self):
        return self.config.get("interaction", {})

    def enter(self):
        self.game.dialogue.load("scene_10")
        w, h = self.game.screen.get_size()
        self.mouth.update(
            float(self.interaction_cfg.get("start_x", w * 0.63)),
            float(self.interaction_cfg.get("start_y", h * 0.57)),
        )

    def handle_input(self, event):
        if self.connected:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            grab_radius = float(self.interaction_cfg.get("grab_radius", 80.0))
            if pygame.Vector2(event.pos).distance_to(self.mouth) <= grab_radius:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            w, h = self.game.screen.get_size()
            min_x = float(self.interaction_cfg.get("min_x", w * 0.29))
            max_x = float(self.interaction_cfg.get("max_x", w * 0.68))
            min_y = float(self.interaction_cfg.get("min_y", h * 0.28))
            max_y = float(self.interaction_cfg.get("max_y", h * 0.76))
            sensitivity = float(self.interaction_cfg.get("drag_sensitivity", 1.0))

            rel = pygame.Vector2(event.rel) * sensitivity
            self.mouth += rel
            self.mouth.x = max(min_x, min(max_x, self.mouth.x))
            self.mouth.y = max(min_y, min(max_y, self.mouth.y))

            sea_edge = w * float(self.interaction_cfg.get("sea_edge_fraction", 0.30))
            snap_distance = float(self.interaction_cfg.get("snap_distance", 34.0))
            if self.mouth.x <= sea_edge + snap_distance:
                # Crossing the threshold commits the metaphor: after the river
                # reaches the sea, input is disabled and the join is irreversible.
                self.mouth.x = sea_edge + 2.0
                self.connected = True
                self.dragging = False

    def update(self, dt):
        self.elapsed += dt
        self.game.dialogue.update(dt)

        if self.connected and self.game.dialogue.finished:
            self.post_complete_elapsed += dt
            delay = float(self.config.get("post_complete_delay", 0.55))
            if self.post_complete_elapsed >= delay and not self.transition_started:
                self.transition_started = True
                self.game.scenes.change_scene(
                    self.config.get("next_scene", "scene_11"),
                    transition_config=self.config.get("transition_out"),
                )
        else:
            self.post_complete_elapsed = 0.0

    def render(self, screen):
        self.renderer.render(
            screen,
            self.mouth.x,
            self.mouth.y,
            self.connected,
            self.elapsed,
        )
        self.game.text_renderer.dialogue(screen, self.game.dialogue)
