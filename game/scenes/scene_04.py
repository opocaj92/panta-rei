import pygame

from game.core.scene import Scene
from game.rendering.river_world_renderer import RiverWorldRenderer
from game.core.world_data import load_world


class Scene04(Scene):
    """Follow the river until its estuary comes into view.

    Navigation and dialogue are independent. Scene 04 completes only while
    the camera has reached the configured horizontal and vertical framing
    thresholds and dialogue has finished. Scene 05 inherits the camera position.
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
        self.min_camera_x = float(estuary["min_camera_x"])
        self.min_camera_y = float(estuary["min_camera_y"])
        self.max_camera_y = float(estuary["max_camera_y"])
        self.estuary_visible = False
        self.flow_time = 0.0

        self.river_points = [tuple(point) for point in world["river_points"]]
        self.river_renderer = RiverWorldRenderer(
            self.world_width,
            self.world_height,
            self.river_points,
            self.game.assets,
        )

    def help_needed(self):
        return not self.estuary_visible and not self.transition_started

    def enter(self):
        self.game.dialogue.load("scene_04")
        # The river is already playing on Scene 02's layer; never restart it.
        fade_ms = round(float(self.config.get("transition_in", {}).get("duration", 0.0)) * 1000)
        self.game.audio.set_ambience_layer_volume("river", 0.18)
        self.game.audio.play_music("scene04_05_piano_theme", fade_ms=fade_ms, volume=0.52)

    def update(self, dt):
        self.game.audio.update_ambience_layers(dt)
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
            self.request_transition(self.config.get("next_scene", "scene_05"), state={"camera": [self.camera.x, self.camera.y], "flow_time": self.flow_time})

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

        self._clamp_camera()

    def pan_touch(self, dx, dy):
        """Move the landscape with the finger during an Android drag."""
        self.camera.x -= dx
        self.camera.y -= dy
        self._clamp_camera()

    def _clamp_camera(self):
        screen_width, screen_height = self.game.screen.get_size()
        max_x = max(0.0, self.world_width - screen_width)
        max_y = max(0.0, self.world_height - screen_height)
        self.camera.x = max(0.0, min(self.camera.x, max_x))
        self.camera.y = max(0.0, min(self.camera.y, max_y))

    def _check_estuary_visibility(self):
        # A bounded Y range prevents finishing with the estuary too high
        # or too low, even if dialogue finishes before camera navigation.
        self.estuary_visible = (
            self.camera.x >= self.min_camera_x
            and self.min_camera_y <= self.camera.y <= self.max_camera_y
        )

    def render(self, screen):
        self.river_renderer.render(
            screen,
            self.camera,
            flow_time=self.flow_time,
            draw_flow=True,
        )
        self.game.text_renderer.dialogue(screen, self.game.dialogue)

