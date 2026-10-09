import pygame




class RiverWorldRenderer:
    """Prototype renderer shared by the river-navigation and estuary scenes."""

    def __init__(self, world_width, world_height, river_points, assets):
        self.assets = assets
        self.world_width = int(world_width)
        self.world_height = int(world_height)
        self.river_points = list(river_points)
        self.frames = self._load_frames()
        self.world_surface = None if self.frames else self._build_world_surface()

    def _load_frames(self):
        """Load aligned full-map animation frames, shared by Scenes 04 and 05."""
        from game.core.config import ASSETS_DIR
        folder = ASSETS_DIR / "scene_04"
        paths = [folder / f"scene04_river_{i:02d}.png" for i in range(1, 5)]
        if not all(path.is_file() for path in paths):
            return []
        frames = [self.assets.image(f"scene_04/river_{i:02d}", f"scene_04/scene04_river_{i:02d}.png", alpha=False, required=True) for i in range(1, 5)]
        expected = (self.world_width, self.world_height)
        if any(frame.get_size() != expected for frame in frames):
            raise ValueError(f"Scene 04 animation frames must be {expected}")
        return frames


    def _build_world_surface(self):
        surface = pygame.Surface((self.world_width, self.world_height))
        surface.fill((14, 25, 37))
        sea_rect = pygame.Rect(1500, 0, self.world_width - 1500, 620)
        pygame.draw.rect(surface, (25, 67, 88), sea_rect)
        pygame.draw.lines(surface, (34, 91, 112), False, self.river_points, 150)
        return surface

    def render(self, screen, camera, flow_time=0.0, draw_flow=True):
        width, height = screen.get_size()
        camera_rect = pygame.Rect(round(camera.x), round(camera.y), width, height)
        if self.frames:
            # Full-map frames already contain the animated river current.
            # No procedural arrows or flow marks should be drawn over them.
            frame = self.frames[int(flow_time * 1.5) % len(self.frames)]
            screen.blit(frame, (0, 0), camera_rect)
        else:
            screen.blit(self.world_surface, (0, 0), camera_rect)
            if draw_flow:
                self._draw_flow_marks(screen, camera, flow_time)

    def _draw_flow_marks(self, screen, camera, flow_time):
        segments = list(zip(self.river_points[:-1], self.river_points[1:]))
        spacing = 105.0
        phase = (flow_time * 75.0) % spacing
        screen_rect = screen.get_rect().inflate(80, 80)

        for start, end in segments:
            start_v = pygame.Vector2(start)
            end_v = pygame.Vector2(end)
            delta = end_v - start_v
            length = delta.length()
            if length == 0:
                continue
            direction = delta / length
            perpendicular = pygame.Vector2(-direction.y, direction.x)
            distance = phase
            while distance < length:
                center = start_v + direction * distance - camera
                if screen_rect.collidepoint(center.x, center.y):
                    tail = center - direction * 18
                    tip = center + direction * 18
                    pygame.draw.line(screen, (112, 157, 171), tail, tip, 3)
                    left = tip - direction * 9 + perpendicular * 7
                    right = tip - direction * 9 - perpendicular * 7
                    pygame.draw.line(screen, (112, 157, 171), tip, left, 3)
                    pygame.draw.line(screen, (112, 157, 171), tip, right, 3)
                distance += spacing
