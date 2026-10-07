class Scene:
    """Common scene lifecycle and optional contextual-help state.

    Subclasses keep ownership of narrative state and mechanics. This base class
    intentionally provides only lifecycle hooks plus the cross-scene help timer.
    """

    HELP_DURATION = 3.0

    def __init__(self, game, config):
        self.game = game
        self.config = config
        self.help_timer = 0.0
        self.incoming_state = {}

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

    def show_help(self):
        if self.get_help_text():
            self.help_timer = self.HELP_DURATION

    def update_help(self, dt):
        self.help_timer = max(0.0, self.help_timer - dt)

    def get_help_text(self):
        """Resolve this scene's help text using the active language and fallbacks."""
        help_cfg = self.config.get("help")
        if not help_cfg:
            return None
        if isinstance(help_cfg, str):
            return help_cfg
        language = getattr(self.game, "language", "en")
        return help_cfg.get(language) or help_cfg.get("en") or help_cfg.get("it")

    def render_help(self, screen):
        if self.help_timer > 0.0:
            self.game.text_renderer.help(screen, self.get_help_text())
