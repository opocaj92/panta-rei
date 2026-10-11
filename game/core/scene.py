class Scene:
    """Common scene lifecycle and optional contextual-help state.

    Subclasses keep ownership of narrative state and mechanics. This base class
    intentionally provides only lifecycle hooks plus the cross-scene help timer.
    Interactive scenes opt into automatic help by overriding ``help_needed`` and
    receive hints after the configured idle period.
    """

    HELP_DELAY = 5.0

    def __init__(self, game, config):
        self.game = game
        self.config = config
        self.reset_help()
        self.incoming_state = {}
        self.transition_started = False

    def reset_help(self):
        """Reset contextual help when a scene is activated or reused."""
        self.help_visible = False
        self.help_wait_elapsed = 0.0

    def request_transition(self, destination, *, state=None, already_faded=False):
        """Request the configured exit transition at most once per scene."""
        if self.transition_started:
            return False
        self.transition_started = True
        kwargs = {"transition_config": None if already_faded else self.config.get("transition_out")}
        if state is not None:
            kwargs["state"] = state
        try:
            self.game.scenes.change_scene(destination, **kwargs)
        except Exception:
            self.transition_started = False
            raise
        return True

    def enter(self):
        pass

    def handle_input(self, event):
        pass

    def update(self, dt):
        pass

    def render(self, screen):
        pass

    def exit(self):
        pass

    def allows_dialogue_advance(self):
        """Whether dialogue is currently presented and can accept advance keys.

        Scenes with a pre-dialogue interaction override this gate.
        """
        return True

    def help_needed(self):
        """Return True only while player action is required to advance the scene."""
        return False

    def update_help(self, dt):
        # The scene's completion criterion alone controls disappearance.
        if not self.get_help_text() or not self.help_needed():
            self.help_wait_elapsed = 0.0
            self.help_visible = False
            return

        if not self.help_visible:
            self.help_wait_elapsed += max(0.0, dt)
            delay = float(self.config.get("help_delay", self.HELP_DELAY))
            if self.help_wait_elapsed >= delay:
                self.help_visible = True

    def get_help_text(self):
        """Resolve this scene's help text using the active language and fallbacks."""
        help_cfg = (self.config.get("touch_help") if getattr(self.game, "touch_enabled", False) else None) or self.config.get("help")
        if not help_cfg:
            return None
        if isinstance(help_cfg, str):
            return help_cfg
        language = getattr(self.game, "language", "en")
        return help_cfg.get(language) or help_cfg.get("en") or help_cfg.get("it")

    def render_help(self, screen):
        if self.help_visible:
            self.game.text_renderer.help(screen, self.get_help_text())

    def render_dialogue_or_thought(self, screen, *, dialogue_rect=None):
        """Use the supported TextRenderer API for authored dialogue types."""
        dialogue = self.game.dialogue
        line = dialogue.current_line
        if line and line.get("type") == "thought":
            self.game.text_renderer.thought(screen, dialogue)
        else:
            self.game.text_renderer.dialogue(screen, dialogue, rect=dialogue_rect)
