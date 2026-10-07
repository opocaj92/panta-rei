class Scene:
    """Common scene lifecycle and optional contextual-help state.

    Subclasses keep ownership of narrative state and mechanics. This base class
    intentionally provides only lifecycle hooks plus the cross-scene help timer.
    Interactive scenes opt into automatic help by overriding ``help_needed`` and
    call ``mark_help_progress`` whenever the player meaningfully advances.
    """

    HELP_DELAY = 5.0
    HELP_DURATION = 3.0

    def __init__(self, game, config):
        self.game = game
        self.config = config
        self.help_timer = 0.0
        self.help_inactivity = 0.0
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

    def help_needed(self):
        """Return True only while player action is required to advance the scene."""
        return False

    def mark_help_progress(self):
        """Restart the inactivity clock after meaningful progress toward completion."""
        self.help_inactivity = 0.0
        self.help_timer = 0.0

    def update_help(self, dt):
        if not self.get_help_text() or not self.help_needed():
            self.help_inactivity = 0.0
            self.help_timer = 0.0
            return

        if self.help_timer > 0.0:
            self.help_timer = max(0.0, self.help_timer - dt)
            return

        self.help_inactivity += dt
        delay = float(self.config.get("help_delay", self.HELP_DELAY))
        if self.help_inactivity >= delay:
            self.help_timer = float(self.config.get("help_duration", self.HELP_DURATION))
            self.help_inactivity = 0.0

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
