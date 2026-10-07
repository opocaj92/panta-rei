import pygame

from game.core.scene import Scene
from game.rendering.river_world_renderer import RiverWorldRenderer
from game.systems.hand_tracing import HandTracingSystem
from game.core.world_data import load_world


class Scene05(Scene):
    """Estuary reflection: freely trace where river might become sea."""

    def __init__(self, game, config):
        super().__init__(game, config)

        world = load_world(config.get("world", "river_estuary"))
        self.world_width = int(world["width"])
        self.world_height = int(world["height"])
        self.river_points = [tuple(point) for point in world["river_points"]]

        framing = config.get("camera", [1400, 0])
        self.camera = pygame.Vector2(float(framing[0]), float(framing[1]))
        self.river_renderer = RiverWorldRenderer(
            self.world_width,
            self.world_height,
            self.river_points,
        )

        self.hand = HandTracingSystem(config.get("tracing", {}))
        self.flow_time = 0.0
        self.post_dialogue_elapsed = 0.0
        self.transition_started = False

    def enter(self):
        # Scene 04 passes its exact final camera position so the scene change
        # is purely an interaction-mode change, with no visual reframing.
        incoming_camera = self.incoming_state.get("camera")
        if incoming_camera is not None:
            self.camera.update(float(incoming_camera[0]), float(incoming_camera[1]))

        self.game.dialogue.load("scene_05")
        self.hand.enter(self.game.screen.get_size())

    def exit(self):
        self.hand.exit()

    def handle_input(self, event):
        if not self.transition_started:
            self.hand.handle_event(event)

    def update(self, dt):
        self.flow_time += dt
        self.hand.update(dt)
        self.game.dialogue.update(dt)

        if self.game.dialogue.finished and not self.transition_started:
            self.post_dialogue_elapsed += dt
            delay = float(self.config.get("post_dialogue_delay", 1.5))
            if self.post_dialogue_elapsed >= delay:
                self.transition_started = True
                self.game.scenes.change_scene(
                    self.config.get("next_scene", "scene_06"),
                    transition_config=self.config.get("transition_out"),
                )

    def render(self, screen):
        self.river_renderer.render(
            screen,
            self.camera,
            flow_time=self.flow_time,
            draw_flow=True,
        )
        self.hand.render_trace(screen)
        self.hand.render_hand(screen)
        self.game.text_renderer.dialogue(screen, self.game.dialogue)

