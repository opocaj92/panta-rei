import pygame


class HandTracingSystem:
    """Mouse-driven pointing hand with temporary, fading trace strokes."""

    def __init__(self, config):
        self.trace_lifetime = float(config.get("trace_lifetime", 2.8))
        self.trace_width = int(config.get("trace_width", 3))
        self.min_point_distance = float(config.get("min_point_distance", 5.0))
        self.hand_position = pygame.Vector2(0, 0)
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

    def render_trace(self, screen):
        if len(self.points) < 2:
            return
        trace_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for i in range(1, len(self.points)):
            p0, age0 = self.points[i - 1]
            p1, age1 = self.points[i]
            # Do not connect strokes across a large mouse jump.
            if p0.distance_to(p1) > 55:
                continue
            age = max(age0, age1)
            alpha = max(0, int(180 * (1.0 - age / self.trace_lifetime)))
            pygame.draw.line(trace_surface, (220, 225, 215, alpha), p0, p1, self.trace_width)
        screen.blit(trace_surface, (0, 0))

    def render_hand(self, screen):
        """Simple prototype arm/hand; replace later with final animation asset."""
        pos = self.hand_position
        shoulder = pygame.Vector2(screen.get_width() * 0.5, screen.get_height() + 35)
        pygame.draw.line(screen, (187, 145, 112), shoulder, pos, 34)
        pygame.draw.circle(screen, (205, 162, 126), (round(pos.x), round(pos.y)), 18)
        # Pointing finger extends slightly beyond the hand toward the cursor.
        direction = pos - shoulder
        if direction.length_squared() == 0:
            direction = pygame.Vector2(0, -1)
        else:
            direction = direction.normalize()
        tip = pos + direction * 32
        pygame.draw.line(screen, (205, 162, 126), pos, tip, 10)
        pygame.draw.circle(screen, (205, 162, 126), (round(tip.x), round(tip.y)), 5)
