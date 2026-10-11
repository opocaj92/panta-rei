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
        self.stroke_ids = []  # Parallel stroke identifiers, one per point.
        self.current_stroke_id = 0
        self.stroke_anchor = None

    def enter(self, screen_size):
        self.hand_position.update(screen_size[0] * 0.62, screen_size[1] * 0.55)
        self.tracing = False
        self.points.clear()
        self.stroke_ids.clear()
        self.current_stroke_id = 0
        self.stroke_anchor = None
        pygame.mouse.set_visible(False)

    def exit(self):
        pygame.mouse.set_visible(True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hand_position.update(event.pos)
            if self.tracing:
                self._record_motion(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hand_position.update(event.pos)
            self.tracing = True
            self.current_stroke_id += 1
            # Do not draw a dot on touch-down. Retain the actual touch position
            # as the anchor for the first movement event.
            self.stroke_anchor = pygame.Vector2(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.hand_position.update(event.pos)
            if self.tracing:
                self._record_motion(event.pos)
            self.tracing = False
            self.stroke_anchor = None

    def _record_motion(self, position):
        pos = pygame.Vector2(position)
        if self.stroke_anchor is None:
            return
        # Ignore stationary touches and tiny sensor jitter. The first real
        # movement creates the anchor and endpoint together, as one stroke.
        if not self.points or self.stroke_ids[-1] != self.current_stroke_id:
            if pos.distance_to(self.stroke_anchor) < self.min_point_distance:
                return
            self._append_point(self.stroke_anchor)
        self._append_point(pos)

    def update(self, dt):
        # Record positions at input-event frequency, not once per rendered frame:
        # otherwise intermediate Android touch samples are silently discarded.
        for point in self.points:
            point[1] += dt
        survivors = [(p, stroke_id) for p, stroke_id in zip(self.points, self.stroke_ids)
                     if p[1] < self.trace_lifetime]
        self.points = [p for p, _ in survivors]
        self.stroke_ids = [stroke_id for _, stroke_id in survivors]

    def _append_point(self, position):
        pos = pygame.Vector2(position)
        if (self.points and self.stroke_ids[-1] == self.current_stroke_id
                and pos.distance_to(self.points[-1][0]) < self.min_point_distance):
            return
        self.points.append([pos, 0.0])
        self.stroke_ids.append(self.current_stroke_id)

    def has_visible_stroke(self):
        """True once a continuous gesture contains a visible segment."""
        return any(
            self.stroke_ids[i - 1] == self.stroke_ids[i]
            and self.points[i - 1][0].distance_to(self.points[i][0]) > 0
            for i in range(1, len(self.points))
        )

    def render_trace(self, screen):
        if len(self.points) < 2:
            return
        trace_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for i in range(1, len(self.points)):
            p0, age0 = self.points[i - 1]
            p1, age1 = self.points[i]
            # Connect every pair within a continuous gesture, even if
            # Android delivers widely spaced touch-motion events.
            if self.stroke_ids[i - 1] != self.stroke_ids[i]:
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
