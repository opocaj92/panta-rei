from game.scenes.black_screen_dialogue import BlackScreenDialogueScene
from game.core.timing import CompletionTimer


class Scene06(BlackScreenDialogueScene):
    """Interlude whose exit delay begins only after dialogue completion."""

    def __init__(self, game, config):
        super().__init__(game, config, "scene_06")
        self.completion_timer = CompletionTimer()

    def enter(self):
        super().enter()
        # Preserve the river layer inherited from Scene 05.
        # The piano was faded during Scene 05's outgoing transition.
        self.completion_timer.reset()

    def update(self, dt):
        self.game.audio.update_ambience_layers(dt)
        super().update(dt)
        if self.game.dialogue.finished and not self.transition_started:
            elapsed = self.completion_timer.update(dt, active=True)
            if elapsed >= float(self.config.get("post_dialogue_delay", 1.0)):
                self.advance_to(self.config.get("next_scene", "scene_07"))
