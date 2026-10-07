from game.core.scene import Scene


class Scene06(Scene):
    """Black-screen interlude: Marco checks whether Stella is listening."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.post_dialogue_elapsed = 0.0
        self.transition_started = False

    def enter(self):
        self.game.dialogue.load("scene_06")

    def update(self, dt):
        self.game.dialogue.update(dt)

        if self.game.dialogue.finished and not self.transition_started:
            self.post_dialogue_elapsed += dt
            delay = float(self.config.get("post_dialogue_delay", 1.0))

            if self.post_dialogue_elapsed >= delay:
                self.transition_started = True
                self.game.scenes.change_scene(
                    self.config.get("next_scene", "scene_07"),
                    transition_config=self.config.get("transition_out"),
                )

    def render(self, screen):
        screen.fill((0, 0, 0))
        self.game.text_renderer.plain(
            screen,
            self.game.dialogue,
            position=self.config.get("text_position", "center"),
            max_width=int(self.config.get("text_max_width", 760)),
        )
