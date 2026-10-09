import pygame

from game.core.scene import Scene
from game.rendering.love_silhouette_renderer import LoveSilhouetteRenderer


class Scene09(Scene):
    """Two profiles approach until their lips touch, pause, then retreat."""

    APPROACHING = "approaching"
    JOINED = "joined"
    SEPARATING = "separating"
    COMPLETE = "complete"

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = LoveSilhouetteRenderer(self.game.assets)
        self.elapsed = 0.0
        self.phase = self.APPROACHING
        self.separation = 0.0
        self.joined_elapsed = 0.0
        self.dragging = False
        self.last_mouse_x = 0
        self.drag_side = None
        self.interaction_finished = False
        self.kiss_flash_elapsed = None
        self.kiss_flash_outline = None
        self.kiss_flash_size = None

    def help_needed(self):
        return self.phase in (self.APPROACHING, self.SEPARATING)

    @property
    def interaction_cfg(self):
        return self.config.get("interaction", {})

    def enter(self):
        self.game.dialogue.load("scene_09")
        self.separation = float(self.interaction_cfg.get("start_separation", 118.0))
        self.kiss_flash_elapsed = None
        self.kiss_flash_outline = None
        self.kiss_flash_size = None
        self.mark_help_progress()

    def handle_input(self, event):
        if self.phase == self.JOINED or self.phase == self.COMPLETE:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            side = self._silhouette_side_at(event.pos)
            if side is not None:
                self.dragging = True
                self.mark_help_progress()
                self.drag_side = side
                self.last_mouse_x = event.pos[0]
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.mark_help_progress()
            self.dragging = False
            self.drag_side = None
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            dx = event.pos[0] - self.last_mouse_x
            self.last_mouse_x = event.pos[0]
            sensitivity = float(self.interaction_cfg.get("drag_sensitivity", 1.0))

            # Dragging either figure changes only its distance from the centre;
            # the counterpart is rendered at the mirrored distance automatically.
            radial_delta = (-dx if self.drag_side == "left" else dx) * sensitivity
            previous_separation = self.separation
            # Directional clamp: during approach only inward motion counts;
            # after the kiss only outward motion counts. Neither can cross.
            if self.phase == self.APPROACHING:
                radial_delta = min(0.0, radial_delta)
            elif self.phase == self.SEPARATING:
                radial_delta = max(0.0, radial_delta)
            self.separation += radial_delta

            if self.phase == self.APPROACHING:
                self.separation = max(0.0, min(self.separation, float(self.interaction_cfg.get("start_separation", 118.0))))
                if self.separation < previous_separation:
                    self.mark_help_progress()
                if self.separation <= float(self.interaction_cfg.get("join_threshold", 3.0)):
                    self.separation = 0.0
                    self.phase = self.JOINED
                    self.joined_elapsed = 0.0
                    # Flash is triggered halfway through the joined pause.
                    self.kiss_flash_elapsed = None
                    self.kiss_flash_outline = None
                    self.dragging = False
            elif self.phase == self.SEPARATING:
                target = float(self.interaction_cfg.get("final_separation", 118.0))
                self.separation = max(0.0, min(self.separation, target))
                if self.separation > previous_separation:
                    self.mark_help_progress()
                if self.separation >= target:
                    self.separation = target
                    self.phase = self.COMPLETE
                    self.interaction_finished = True
                    self.dragging = False

    def _silhouette_side_at(self, pos):
        return self.renderer.side_at(self.game.screen, pos, self.separation)

    def update(self, dt):
        self.elapsed += dt
        if self.kiss_flash_elapsed is not None:
            self.kiss_flash_elapsed += dt
            if self.kiss_flash_elapsed >= 0.55:
                self.kiss_flash_elapsed = None
                self.kiss_flash_outline = None
        self.game.dialogue.update(dt)

        if self.phase == self.JOINED:
            # JOINED deliberately ignores input: the temporary lock embodies the
            # dialogue's instant of union before separation becomes possible.
            previous_joined_elapsed = self.joined_elapsed
            self.joined_elapsed += dt
            joined_duration = float(self.interaction_cfg.get("joined_lock_duration", 2.0))
            midpoint = joined_duration / 2.0
            if previous_joined_elapsed < midpoint <= self.joined_elapsed:
                # Start precisely when the joined pause crosses its midpoint.
                self.kiss_flash_elapsed = self.joined_elapsed - midpoint
                self.kiss_flash_outline = None
            if self.joined_elapsed >= joined_duration:
                self.phase = self.SEPARATING
                self.mark_help_progress()

        if self.game.dialogue.finished and self.interaction_finished and not self.transition_started:
            self.request_transition(self.config.get("next_scene", "scene_10"))

    def _draw_kiss_flash(self, screen):
        """A brief pixel-sharp halo around the *combined* joined silhouettes."""
        if self.kiss_flash_elapsed is None:
            return
        size = screen.get_size()
        if self.kiss_flash_outline is None or self.kiss_flash_size != size:
            # Compose the two opaque shapes into one mask, so the glow follows
            # their shared exterior instead of drawing two overlapping halos.
            boy_rect, girl_rect = self.renderer.rects(screen, 0.0)
            left = max(0, min(boy_rect.left, girl_rect.left) - 6)
            top = max(0, min(boy_rect.top, girl_rect.top) - 6)
            right = min(size[0], max(boy_rect.right, girl_rect.right) + 6)
            bottom = min(size[1], max(boy_rect.bottom, girl_rect.bottom) + 6)
            if right <= left or bottom <= top:
                return
            shape = pygame.Surface((right - left, bottom - top), pygame.SRCALPHA)
            shape.blit(self.renderer.boy, (boy_rect.left - left, boy_rect.top - top))
            shape.blit(self.renderer.girl, (girl_rect.left - left, girl_rect.top - top))
            mask = pygame.mask.from_surface(shape, 30)
            points = mask.outline()
            if len(points) < 2:
                return
            outline = pygame.Surface(shape.get_size(), pygame.SRCALPHA)
            # Both passes use hard pixel edges; the low-alpha wider line is
            # the halo, while the narrower stroke gives the kiss its sparkle.
            pygame.draw.lines(outline, (235, 240, 255, 65), True, points, 5)
            pygame.draw.lines(outline, (255, 250, 238, 220), True, points, 2)
            self.kiss_flash_outline = (outline, (left, top))
            self.kiss_flash_size = size

        t = self.kiss_flash_elapsed
        # Rise to full intensity in 0.15s, then fade over the next 0.40s.
        strength = min(1.0, t / 0.15) if t < 0.15 else max(0.0, (0.55 - t) / 0.40)
        outline, pos = self.kiss_flash_outline
        outline.set_alpha(round(255 * strength))
        screen.blit(outline, pos)

    def render(self, screen):
        self.renderer.render(screen, self.separation, self.phase, self.elapsed)
        self._draw_kiss_flash(screen)
        line = self.game.dialogue.current_line
        if line and line.get("type") == "thought":
            self.game.text_renderer.thought(screen, self.game.dialogue)
        else:
            self.game.text_renderer.dialogue(screen, self.game.dialogue)
