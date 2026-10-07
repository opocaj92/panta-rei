import pygame

from game.core.scene import Scene
from game.rendering.love_silhouette_renderer import LoveSilhouetteRenderer


class Scene09(Scene):
    """Two mirrored silhouettes meet, remain joined, then must separate again."""

    APPROACHING = "approaching"
    JOINED = "joined"
    SEPARATING = "separating"
    COMPLETE = "complete"

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = LoveSilhouetteRenderer()
        self.elapsed = 0.0
        self.phase = self.APPROACHING
        self.separation = 0.0
        self.joined_elapsed = 0.0
        self.dragging = False
        self.last_mouse_x = 0
        self.drag_side = None
        self.interaction_finished = False
        self.transition_started = False

    @property
    def interaction_cfg(self):
        return self.config.get("interaction", {})

    def enter(self):
        self.game.dialogue.load("scene_09")
        self.separation = float(self.interaction_cfg.get("start_separation", 260.0))

    def handle_input(self, event):
        if self.phase == self.JOINED or self.phase == self.COMPLETE:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            side = self._silhouette_side_at(event.pos)
            if side is not None:
                self.dragging = True
                self.drag_side = side
                self.last_mouse_x = event.pos[0]
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            self.drag_side = None
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dx = event.pos[0] - self.last_mouse_x
            self.last_mouse_x = event.pos[0]
            sensitivity = float(self.interaction_cfg.get("drag_sensitivity", 1.0))

            # Dragging either figure changes only its distance from the centre;
            # the counterpart is rendered at the mirrored distance automatically.
            radial_delta = (-dx if self.drag_side == "left" else dx) * sensitivity
            self.separation += radial_delta

            if self.phase == self.APPROACHING:
                self.separation = max(0.0, min(self.separation, float(self.interaction_cfg.get("start_separation", 260.0))))
                if self.separation <= float(self.interaction_cfg.get("join_threshold", 4.0)):
                    self.separation = 0.0
                    self.phase = self.JOINED
                    self.joined_elapsed = 0.0
                    self.dragging = False
            elif self.phase == self.SEPARATING:
                target = float(self.interaction_cfg.get("final_separation", 260.0))
                self.separation = max(0.0, min(self.separation, target))
                if self.separation >= target:
                    self.separation = target
                    self.phase = self.COMPLETE
                    self.interaction_finished = True
                    self.dragging = False

    def _silhouette_side_at(self, pos):
        w, h = self.game.screen.get_size()
        y = h // 2 + 25
        grab_radius = float(self.interaction_cfg.get("grab_radius", 90.0))
        candidates = (("left", w // 2 - self.separation), ("right", w // 2 + self.separation))
        for side, x in candidates:
            if (pos[0] - x) ** 2 + (pos[1] - y) ** 2 <= grab_radius ** 2:
                return side
        return None

    def update(self, dt):
        self.elapsed += dt
        self.game.dialogue.update(dt)

        if self.phase == self.JOINED:
            # JOINED deliberately ignores input: the temporary lock embodies the
            # dialogue's instant of union before separation becomes possible.
            self.joined_elapsed += dt
            if self.joined_elapsed >= float(self.interaction_cfg.get("joined_lock_duration", 2.0)):
                self.phase = self.SEPARATING

        if self.game.dialogue.finished and self.interaction_finished and not self.transition_started:
            self.transition_started = True
            self.game.scenes.change_scene(
                self.config.get("next_scene", "scene_10"),
                transition_config=self.config.get("transition_out"),
            )

    def render(self, screen):
        self.renderer.render(screen, self.separation, self.phase, self.elapsed)
        line = self.game.dialogue.current_line
        if line and line.get("type") == "thought":
            self.game.text_renderer.thought(screen, self.game.dialogue)
        else:
            self.game.text_renderer.dialogue(screen, self.game.dialogue)
