"""Shared presentation for narrative interludes on a black screen."""

from game.core.scene import Scene


class BlackScreenDialogueScene(Scene):
    def __init__(self, game, config, dialogue_id):
        super().__init__(game, config)
        self.dialogue_id = dialogue_id

    def enter(self):
        self.game.dialogue.load(self.dialogue_id)

    def update(self, dt):
        self.game.dialogue.update(dt)

    def advance_to(self, destination):
        self.request_transition(destination)

    def render(self, screen):
        screen.fill((0, 0, 0))
        self.game.text_renderer.plain(
            screen,
            self.game.dialogue,
            position=self.config.get("text_position", "center"),
            max_width=int(self.config.get("text_max_width", 486)),
        )
