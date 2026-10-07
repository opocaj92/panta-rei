import pygame

from game.core.scene import Scene
from game.rendering.river_world_renderer import RiverWorldRenderer
from game.core.world_data import load_world


class Scene04(Scene):
    """Follow the river until its estuary comes into view.

    Navigation and dialogue are independent. Scene 04 completes only while
    enough of the configured estuary region is CURRENTLY visible and the
    dialogue has finished. Scene 05 then inherits that exact camera position.
    """

    def __init__(self, game, config):
        super().__init__(game, config)

        world = load_world(config.get("world", "river_estuary"))
        self.world_width = int(world["width"])
        self.world_height = int(world["height"])

        start = config.get("camera_start", [0, 1500])
        self.camera = pygame.Vector2(float(start[0]), float(start[1]))
        self.camera_speed = float(config.get("camera_speed", 360.0))

        estuary = config.get("estuary", {})
        region = world["estuary_region"]
        self.estuary_region = pygame.Rect(*map(int, region))
        self.required_visible_fraction = float(
            estuary.get("required_visible_fraction", 0.35)
        )

        self.estuary_visible = False
        self.best_estuary_distance = float("inf")
        self.best_visible_fraction = 0.0
        self.transition_started = False
        self.flow_time = 0.0

        self.river_points = [tuple(point) for point in world["river_points"]]
        self.river_renderer = RiverWorldRenderer(
            self.world_width,
            self.world_height,
            self.river_points,
        )

    def help_needed(self):
        return not self.estuary_visible and not self.transition_started

    def enter(self):
        self.game.dialogue.load("scene_04")

    def update(self, dt):
        self.flow_time += dt

        # Reaching the estuary does NOT lock navigation. The player may keep
        # moving while the remaining dialogue unfolds.
        self._update_camera(dt)
        self._check_estuary_visibility()

        self.game.dialogue.update(dt)

        if (
            self.estuary_visible
            and self.game.dialogue.finished
            and not self.transition_started
        ):
            self.transition_started = True
            self.game.scenes.change_scene(
                self.config.get("next_scene", "scene_05"),
                transition_config=self.config.get("transition_out"),
                state={"camera": [self.camera.x, self.camera.y]},
            )

    def _update_camera(self, dt):
        direction = pygame.Vector2(0.0, 0.0)

        if self.game.input.held(pygame.K_LEFT) or self.game.input.held(pygame.K_a):
            direction.x -= 1.0
        if self.game.input.held(pygame.K_RIGHT) or self.game.input.held(pygame.K_d):
            direction.x += 1.0
        if self.game.input.held(pygame.K_UP) or self.game.input.held(pygame.K_w):
            direction.y -= 1.0
        if self.game.input.held(pygame.K_DOWN) or self.game.input.held(pygame.K_s):
            direction.y += 1.0

        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.camera += direction * self.camera_speed * dt

        screen_width, screen_height = self.game.screen.get_size()
        max_x = max(0.0, self.world_width - screen_width)
        max_y = max(0.0, self.world_height - screen_height)
        self.camera.x = max(0.0, min(self.camera.x, max_x))
        self.camera.y = max(0.0, min(self.camera.y, max_y))

    def _check_estuary_visibility(self):
        # This is deliberately NOT latched. If the player finds the estuary and
        # then moves away, Scene 04 must wait until enough of it is visible again.
        screen_width, screen_height = self.game.screen.get_size()
        viewport = pygame.Rect(
            round(self.camera.x),
            round(self.camera.y),
            screen_width,
            screen_height,
        )
        visible = viewport.clip(self.estuary_region)
        region_area = self.estuary_region.width * self.estuary_region.height
        visible_area = visible.width * visible.height
        visible_fraction = visible_area / region_area if region_area else 0.0

        viewport_center = pygame.Vector2(viewport.center)
        estuary_center = pygame.Vector2(self.estuary_region.center)
        distance = viewport_center.distance_to(estuary_center)
        if (
            distance < self.best_estuary_distance - 1.0
            or visible_fraction > self.best_visible_fraction + 0.001
        ):
            self.best_estuary_distance = min(self.best_estuary_distance, distance)
            self.best_visible_fraction = max(self.best_visible_fraction, visible_fraction)
            self.mark_help_progress()

        self.estuary_visible = visible_fraction >= self.required_visible_fraction

    def render(self, screen):
        self.river_renderer.render(
            screen,
            self.camera,
            flow_time=self.flow_time,
            draw_flow=True,
        )
        self.game.text_renderer.dialogue(screen, self.game.dialogue)

