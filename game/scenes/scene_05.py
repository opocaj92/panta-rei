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
        self.has_drawn_stroke = False
        self.resolution_started = False
        self.resolution_finished = False
        self.paint_idle_time = 0.0
        self.paint_active = False

    def help_needed(self):
        # A visible stroke teaches the mechanic; never repeat the hint.
        return not self.has_drawn_stroke and not self.transition_started

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
        self.has_drawn_stroke = False
        self.resolution_started = False
        self.resolution_finished = False
        self.paint_idle_time = 0.0
        self.paint_active = False
        # Keep Scene 04's river layer at its established level without restarting it.
        self.game.audio.set_ambience_layer_volume("river", 0.18)
        # Scene 04's river keeps playing; at the scene boundary the piano
        # yields once to the resolution phrase, then resumes from its pause.
        self._start_resolution()

    def exit(self):
        self.game.audio.fade_sfx("scene05_wet_brushstroke", fade_ms=120)
        self.hand.exit()

    def handle_input(self, event):
        if self.transition_started:
            return
        if event.type == pygame.MOUSEMOTION and self.hand.tracing:
            # Only actual drawn movement makes the brush audible.
            previous = self.hand.hand_position
            distance = pygame.Vector2(event.pos).distance_to(previous)
            if distance >= self.hand.min_point_distance:
                self.paint_idle_time = 0.0
                if not self.paint_active:
                    self.paint_active = self.game.audio.play_loop_sfx(
                        "scene05_wet_brushstroke", volume=0.23)
                else:
                    self.game.audio.set_sfx_volume("scene05_wet_brushstroke", 0.23)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._stop_paint_sound()
        self.hand.handle_event(event)

    def _stop_paint_sound(self):
        if self.paint_active:
            self.game.audio.fade_sfx("scene05_wet_brushstroke", fade_ms=120)
            self.paint_active = False

    def update(self, dt):
        self.game.audio.update_ambience_layers(dt)
        self.flow_time += dt
        self.hand.update(dt)
        if self.paint_active:
            self.paint_idle_time += dt
            if not self.hand.tracing or self.paint_idle_time > 0.16:
                self._stop_paint_sound()
        # Any genuine drawn segment satisfies the interaction requirement.
        if self.hand.has_visible_stroke():
            self.has_drawn_stroke = True

        self.game.dialogue.update(dt)
        if self.resolution_started and not self.resolution_finished:
            if not self.game.audio.is_sfx_playing("scene05_piano_resolution"):
                self.resolution_finished = True
                if not self.transition_started:
                    self.game.audio.resume_music()

        if self.game.dialogue.finished and self.has_drawn_stroke and not self.transition_started:
            elapsed = self.completion_timer.update(dt, active=True)
            delay = float(self.config.get("post_dialogue_delay", 1.5))
            if elapsed >= delay:
                # Fade the soundscape as the eye blink closes, not on Scene 06 entry.
                fade_ms = round(float(self.config.get("transition_out", {}).get("duration", 0.0)) * 1000)
                self._stop_paint_sound()
                self.game.audio.stop_music(fade_ms=fade_ms)
                # Keep the same river channel running into the black-screen Scene 06.
                self.game.audio.fade_sfx("scene05_piano_resolution", fade_ms=fade_ms)
                self.request_transition(self.config.get("next_scene", "scene_06"))

    def _start_resolution(self):
        if self.resolution_started:
            return
        self.resolution_started = True
        # The theme is suspended, not restarted: resume at the same point.
        self.game.audio.pause_music()
        if not self.game.audio.play_sfx("scene05_piano_resolution", volume=0.30):
            self.resolution_finished = True
            self.game.audio.resume_music()

    def render(self, screen):
        self.river_renderer.render(
            screen,
            self.camera,
            flow_time=self.flow_time,
            draw_flow=True,
        )
        self.hand.render_trace(screen)
        if not getattr(self.game, "touch_enabled", False):
            self.hand.render_hand(screen)
        self.game.text_renderer.dialogue(screen, self.game.dialogue)

