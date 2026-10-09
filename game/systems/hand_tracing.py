import pygame


class HandTracingSystem:
    """Mouse-driven pointing hand with temporary, fading trace strokes."""

    def __init__(self, config, assets):
        self.trace_lifetime = float(config.get("trace_lifetime", 2.8))
        self.trace_width = int(config.get("trace_width", 3))
        self.min_point_distance = float(config.get("min_point_distance", 5.0))
        self.hand_position = pygame.Vector2(0, 0)
        self.arm_sprite = assets.image('scene_05/marco_pointing_arm', 'scene_05/marco_pointing_arm.png', required=True)
        # Fingertip position in the cropped 360px-high sprite.
        self.fingertip = pygame.Vector2(184, 2)
        self.tracing = False
        self.points = []  # [Vector2, age]

    def enter(self, screen_size):
        self.hand_position.update(screen_size[0] * 0.62, screen_size[1] * 0.55)
        self.tracing = False
        self.points.clear()
        pygame.mouse.set_visible(False)

    def exit(self):
        pygame.mouse.set_visible(True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hand_position.update(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.tracing = True
            self._append_point(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.tracing = False

    def update(self, dt):
        self.hand_position.update(pygame.mouse.get_pos())
        for point in self.points:
            point[1] += dt
        self.points = [p for p in self.points if p[1] < self.trace_lifetime]
        if self.tracing:
            self._append_point(self.hand_position)

    def _append_point(self, position):
        pos = pygame.Vector2(position)
        if self.points and pos.distance_to(self.points[-1][0]) < self.min_point_distance:
            return
        self.points.append([pos, 0.0])

    def has_visible_stroke(self):
        """True once at least one segment meets the trace renderer's criteria."""
        return any(
            0 < self.points[i - 1][0].distance_to(self.points[i][0]) <= 34
            for i in range(1, len(self.points))
        )

    def render_trace(self, screen):
        if len(self.points) < 2:
            return
        trace_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for i in range(1, len(self.points)):
            p0, age0 = self.points[i - 1]
            p1, age1 = self.points[i]
            # Do not connect strokes across a large mouse jump.
            if p0.distance_to(p1) > 34:
                continue
            age = max(age0, age1)
            alpha = max(0, int(180 * (1.0 - age / self.trace_lifetime)))
            pygame.draw.line(trace_surface, (220, 225, 215, alpha), p0, p1, self.trace_width)
        screen.blit(trace_surface, (0, 0))

    def render_hand(self, screen):
        """Draw Marco's pointing arm with the fingertip at the mouse position.

        The sprite extends below the viewport when the cursor is lower, so
        pygame clips the unseen portion naturally.
        """
        pos = self.hand_position
        screen.blit(self.arm_sprite, (
            round(pos.x - self.fingertip.x),
            round(pos.y - self.fingertip.y),
        ))
