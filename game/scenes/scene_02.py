import pygame

from game.core.scene import Scene
from game.rendering.renderer import PrototypeRenderer
from game.systems.gaze import GazeSystem


class Scene02(Scene):
    """
    Marco's POV.

    Presentation belongs to the scene (`current_view`). GazeSystem only
    interprets directional input. Puzzle timings and available views come
    from this scene's JSON configuration.
    """

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = PrototypeRenderer()

        self.views = list(config.get("views", []))
        self.sky_view = config.get("sky_view")
        self.current_view = config.get("initial_view")

        if not self.views:
            raise ValueError("scene_02 requires a non-empty 'views' list")
        if self.current_view not in self.views:
            raise ValueError("scene_02 'initial_view' must be one of 'views'")

        self.gaze = GazeSystem(
            self.views,
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
        self.transition_started = False

    def enter(self):
        self.game.dialogue.load("scene_02")

    def handle_input(self, event):
        if self.progress_complete or event.type != pygame.KEYDOWN:
            return

        requested_view = self.gaze.handle_key(event.key)
        if requested_view is not None:
            self.current_view = requested_view

    def update(self, dt):
        if not self.progress_complete:
            if self.current_view == self.stella_view:
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
            self.transition_started = True
            self.game.scenes.change_scene(
                "scene_03",
                transition_config=self.config.get("transition_out"),
            )

    def render(self, screen):
        self.renderer.background(screen, self.current_view)

        if self.progress_complete and self.dialogue_started:
            self.game.text_renderer.dialogue(screen, self.game.dialogue)
