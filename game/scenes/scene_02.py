import pygame
import random

from game.core.scene import Scene
from game.rendering.marco_pov_renderer import MarcoPOVRenderer
from game.systems.gaze import GazeSystem


class Scene02(Scene):
    RUSTLE_SOUNDS = ("scene02_clothing_rustle_01", "scene02_clothing_rustle_02", "scene02_clothing_rustle_03")
    RUSTLE_VOLUME = 0.36

    AUDIO_LAYERS = {
        "river": "scene02_river",
        "wind": "scene01_night_wind",
        "vegetation": "scene02_vegetation",
        "phone": "scene02_phone",
    }
    VIEW_MIX = {
        "river": {"river": 0.32, "wind": 0.22, "vegetation": 0.08, "phone": 0.08},
        "stella": {"river": 0.12, "wind": 0.18, "vegetation": 0.05, "phone": 0.65},
        "grass": {"river": 0.08, "wind": 0.32, "vegetation": 0.80, "phone": 0.02},
        "city": {"river": 0.09, "wind": 0.35, "vegetation": 0.10, "phone": 0.02},
        "sky": {"river": 0.07, "wind": 0.48, "vegetation": 0.05, "phone": 0.0},
    }

    """
    Marco's POV.

    Presentation belongs to the scene (`current_view`). GazeSystem only
    interprets directional input. Puzzle timings and available views come
    from this scene's JSON configuration.
    """

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = MarcoPOVRenderer(game.assets, config)

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

        sequence = config.get("attention_sequence", [])
        if len(sequence) < 2:
            raise ValueError("scene_02 requires two attention_sequence steps")

        self.stella_view = sequence[0]["view"]
        self.stella_required = float(sequence[0]["duration"])
        self.river_view = sequence[1]["view"]
        self.river_required = float(sequence[1]["duration"])

        self.stella_attention = 0.0
        self.river_attention = 0.0
        self.stella_seen = False
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
        self.game.audio.start_ambience_layers(self.AUDIO_LAYERS)
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
            # View navigation is active exploration, not inactivity. Reset the
            # contextual-help clock and dismiss any currently visible hint.

            if requested_view != self.current_view:
                self.current_view = requested_view
                self.game.audio.play_sfx(random.choice(self.RUSTLE_SOUNDS), volume=self.RUSTLE_VOLUME)
                self._set_view_mix(fade_ms=800)

    def _set_view_mix(self, *, fade_ms):
        mix = self.VIEW_MIX.get(self.current_view, self.VIEW_MIX["river"])
        for name in self.AUDIO_LAYERS:
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
            if self.current_view == self.stella_view:
                if not self.stella_seen:
                    self.stella_attention += dt

                    if self.stella_attention >= self.stella_required:
                        self.stella_seen = True


            elif self.current_view == self.river_view and self.stella_seen:
                self.river_attention += dt

                if self.river_attention >= self.river_required:
                    self.progress_complete = True
                    self.dialogue_delay = float(
                        self.config.get("dialogue_start_delay", 0.8)
                    )
            return

        if self.dialogue_delay > 0:
            self.dialogue_delay -= dt
            return

        self.dialogue_started = True
        self.game.dialogue.update(dt)

        if self.game.dialogue.finished and not self.transition_started:
            fade_ms = round(float(self.config.get("transition_out", {}).get("duration", 0.0)) * 1000)
            for name in self.AUDIO_LAYERS:
                target = 0.32 if name == "river" else 0.0
                self.game.audio.set_ambience_layer_volume(name, target, fade_ms=fade_ms)
            self.request_transition("scene_03")

    def render(self, screen):
        self.renderer.render(screen, self.current_view)

        if self.progress_complete and self.dialogue_started:
            self.game.text_renderer.dialogue(screen, self.game.dialogue)
