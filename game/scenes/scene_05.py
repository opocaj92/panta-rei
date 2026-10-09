import pygame

from game.core.scene import Scene
from game.core.timing import CompletionTimer
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
            self.game.assets,
        )

        self.hand = HandTracingSystem(config.get("tracing", {}), game.assets)
        self.flow_time = 0.0
        self.completion_timer = CompletionTimer()
        self.has_traced_line = False

    def help_needed(self):
        # A visible stroke teaches the mechanic; never repeat the hint.
        return not self.has_traced_line and not self.transition_started and not self.game.dialogue.finished

    def enter(self):
        # Scene 04 passes its exact final camera position so the scene change
        # is purely an interaction-mode change, with no visual reframing.
        incoming_camera = self.incoming_state.get("camera")
        if incoming_camera is not None:
            self.camera.update(float(incoming_camera[0]), float(incoming_camera[1]))

        # Continue the same water-animation phase as Scene 04.
        self.flow_time = float(self.incoming_state.get("flow_time", 0.0))

        self.game.dialogue.load("scene_05")
        self.hand.enter(self.game.screen.get_size())
        self.has_traced_line = False

    def exit(self):
        self.hand.exit()

    def handle_input(self, event):
        if not self.transition_started:
            self.hand.handle_event(event)
            # A press begins a genuine drawing attempt; hide the hint now,
            # rather than waiting for the first rendered line segment.
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mark_help_progress()
            # Require a genuine visible stroke, not a click or mouse movement.
            # Points may fade, so remember successful tracing for the whole scene.
            if not self.has_traced_line and self.hand.has_visible_stroke():
                self.has_traced_line = True
                self.mark_help_progress()

    def update(self, dt):
        self.flow_time += dt
        self.hand.update(dt)
        if not self.has_traced_line and self.hand.has_visible_stroke():
            self.has_traced_line = True
            self.mark_help_progress()
        self.game.dialogue.update(dt)

        if self.game.dialogue.finished and not self.transition_started:
            elapsed = self.completion_timer.update(dt, active=True)
            delay = float(self.config.get("post_dialogue_delay", 1.5))
            if elapsed >= delay:
                self.request_transition(self.config.get("next_scene", "scene_06"))

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

