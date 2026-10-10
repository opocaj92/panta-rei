from game.scenes.black_screen_dialogue import BlackScreenDialogueScene


class Scene03(BlackScreenDialogueScene):
    """Interlude whose minimum duration is measured from scene entry."""

    def __init__(self, game, config):
        super().__init__(game, config, "scene_03")
        self.elapsed = 0.0

    def enter(self):
        super().enter()
        # Keep the same river playback from Scene 02; all other layers fade away.
        self.game.audio.set_ambience_layer_volume("river", 0.18)
        for name in ("wind", "vegetation", "phone"):
            self.game.audio.set_ambience_layer_volume(name, 0.0, fade_ms=250)
        self.elapsed = 0.0

    def update(self, dt):
        super().update(dt)
        self.game.audio.update_ambience_layers(dt)
        self.elapsed += dt
        if self.elapsed >= float(self.config.get("auto_delay", 1.5)) and self.game.dialogue.finished:
            self.advance_to("scene_04")
