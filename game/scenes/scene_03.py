from game.core.scene import Scene


class Scene03(Scene):
    """Black-screen interlude: 'Ma che vuol dire davvero...'"""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.elapsed = 0.0
        self.transition_started = False

    def enter(self):
        self.elapsed = 0.0
        self.transition_started = False
        self.game.dialogue.load("scene_03")

    def update(self, dt):
        self.elapsed += dt
        self.game.dialogue.update(dt)

        auto_delay = float(self.config.get("auto_delay", 1.5))
        if (
            self.elapsed >= auto_delay
            and self.game.dialogue.finished
            and not self.transition_started
        ):
            self.transition_started = True
            self.game.scenes.change_scene(
                "scene_04",
                transition_config=self.config.get("transition_out"),
            )

    def render(self, screen):
        # Game clears the frame to black before scene rendering.
        screen.fill((0, 0, 0))
        self.game.text_renderer.plain(
            screen,
            self.game.dialogue,
            position=self.config.get("text_position", "center"),
            max_width=int(self.config.get("text_max_width", 760)),
        )
