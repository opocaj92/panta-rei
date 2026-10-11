import pygame
import random

from game.core.scene import Scene
from game.core.riverbank_audio import riverbank_audio, riverbank_mix
from game.rendering.marco_pov_renderer import MarcoPOVRenderer
from game.systems.gaze import GazeSystem


class Scene02(Scene):
    """Marco's POV: explore every view before returning to the river for dialogue."""

    RUSTLE_SOUNDS = ("scene02_clothing_rustle_01", "scene02_clothing_rustle_02", "scene02_clothing_rustle_03")

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = MarcoPOVRenderer(game.assets, config)
        self.audio_layers = riverbank_audio()["layers"]
        self.rustle_volume = float(config.get("rustle_volume", 0.36))

        self.horizontal_views = list(config.get("horizontal_views", []))
        self.sky_view = config.get("sky_view")
        self.current_view = config.get("initial_view")

        if not self.horizontal_views:
            raise ValueError("scene_02 requires a non-empty 'horizontal_views' list")
        if self.current_view not in self.horizontal_views:
            raise ValueError("scene_02 'initial_view' must be one of 'horizontal_views'")

        self.gaze = GazeSystem(
            self.horizontal_views,
            sky_view=self.sky_view,
            initial_view=self.current_view,
        )

        self.river_view = "river"
        if self.river_view not in self.horizontal_views:
            raise ValueError("scene_02 requires a 'river' horizontal view")
        self.required_views = set(self.horizontal_views)
        if self.sky_view is not None:
            self.required_views.add(self.sky_view)
        self.visited_views = {self.current_view}
        self.progress_complete = False
        self.dialogue_delay = 0.0
        self.dialogue_started = False

    def allows_dialogue_advance(self):
        return self.progress_complete and self.dialogue_started and not self.transition_started

    def help_needed(self):
        return not self.progress_complete

    def enter(self):
        self.renderer.reset()
        self.game.dialogue.load("scene_02")
        # The opening wind stays audible until this scene is activated.
        # Fade it out while the new layers fade in, avoiding a silent gap.
        self.game.audio.stop_ambience(fade_ms=900)
        self.game.audio.start_ambience_layers(self.audio_layers)
        self._set_view_mix(fade_ms=900)

    def handle_input(self, event):
        if self.progress_complete or event.type != pygame.KEYDOWN:
            return

        # While looking at the sky, only Down/S can return to the
        # previous horizontal view. Ignore sideways (and Up) navigation.
        if self.current_view == self.sky_view and event.key not in (
            pygame.K_DOWN, pygame.K_s
        ):
            return

        requested_view = self.gaze.handle_key(event.key)
        if requested_view is not None:
            if requested_view != self.current_view:
                self.current_view = requested_view
                self.visited_views.add(requested_view)
                self.game.audio.play_sfx(random.choice(self.RUSTLE_SOUNDS), volume=self.rustle_volume)
                self._set_view_mix(fade_ms=800)
                # Lock the gaze on the river as soon as all views have been
                # explored; preserve the existing pause before dialogue.
                if (self.current_view == self.river_view
                        and self.required_views.issubset(self.visited_views)):
                    self.progress_complete = True
                    self.dialogue_delay = float(self.config.get("dialogue_start_delay", 0.8))

    def _set_view_mix(self, *, fade_ms):
        mix = riverbank_mix(self.current_view if self.current_view in riverbank_audio()["mixes"] else "river")
        for name in self.audio_layers:
            self.game.audio.set_ambience_layer_volume(
                name, mix.get(name, 0.0), fade_ms=fade_ms
            )

    def exit(self):
        # Preserve the river channel and its exact playback position for Scenes 03–05.
        pass

    def update(self, dt):
        self.game.audio.update_ambience_layers(dt)
        # The renderer receives the current presentation view so random visual
        # events can start only when they are actually observable.
        self.renderer.update(dt, self.current_view)

        if not self.progress_complete:
            return

        if self.dialogue_delay > 0:
            self.dialogue_delay -= dt
            return

        self.dialogue_started = True
        self.game.dialogue.update(dt)

        if self.game.dialogue.finished and not self.transition_started:
            fade_ms = round(float(self.config.get("transition_out", {}).get("duration", 0.0)) * 1000)
            for name in self.audio_layers:
                target = 0.18 if name == "river" else 0.0
                self.game.audio.set_ambience_layer_volume(name, target, fade_ms=fade_ms)
            self.request_transition("scene_03")

    def render(self, screen):
        self.renderer.render(screen, self.current_view)

        if self.progress_complete and self.dialogue_started:
            self.game.text_renderer.dialogue(screen, self.game.dialogue)
