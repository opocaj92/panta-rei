import math

from game.core.scene import Scene
from game.rendering.stella_pov_renderer import StellaPOVRenderer
from game.rendering.phone_credits_renderer import PhoneCreditsRenderer


class Scene12(Scene):
    """Final credits, projected onto Stella's tilted phone display."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = StellaPOVRenderer(config, game.assets)
        self.credits_renderer = PhoneCreditsRenderer(game.assets, config.get("credits_display", {}), typography=game.typography)
        self.phone_overlay = game.assets.image('scene_12/phone_credits', 'scene_12/phone_credits.png', required=True)
        self.elapsed = 0.0
        self.phase = 'title'
        self.phase_time = 0.0
        self.scroll_y = 0.0
        self.fade_started = False
        self.terminal_black = False
        self._build_credits()

    def enter(self):
        self.elapsed = 0.0
        self.phase = 'title'
        self.phase_time = 0.0
        self.scroll_y = float(self.credits_renderer.glass.height + 8)
        self.fade_started = False
        self.terminal_black = False
        self._build_credits()

    def handle_input(self, event):
        return

    def _build_credits(self):
        language = getattr(self.game, 'language', 'en')
        entries = self.config.get('credits_by_language', {}).get(language)
        if entries is None:
            entries = self.config.get('credits_by_language', {}).get('en', [])
        self.credits_renderer.set_credits(entries)

    def update(self, dt):
        self.elapsed += dt
        if self.terminal_black:
            return
        self.phase_time += dt
        if self.phase == 'title':
            if self.phase_time >= float(self.config.get('opening_title_duration', 2.7)):
                self.phase, self.phase_time = 'scroll', 0.0
            return
        if self.phase == 'scroll':
            speed = float(self.config.get('scroll_speed', 17.0))
            # Smooth acceleration from the opening title; gentle speed variation
            # keeps the names legible without abrupt stop/start jumps.
            ramp = min(1.0, self.phase_time / 1.1)
            ramp = ramp * ramp * (3 - 2 * ramp)
            cadence = 0.90 + 0.10 * math.cos(self.scroll_y / 42.0)
            self.scroll_y -= speed * ramp * cadence * dt
            if self.scroll_y + self.credits_renderer.credit_height <= -12:
                self.phase, self.phase_time = 'final', 0.0
            return
        if self.phase == 'final' and not self.fade_started:
            if self.phase_time >= float(self.config.get('final_hold_duration', 3.0)):
                self.fade_started = True
                transition = self.config.get('transition_out', {})
                self.game.transitions.fade_to_black(
                    float(transition.get('duration', 1.5)), on_complete=self._finish)

    def _finish(self):
        self.terminal_black = True

    def render(self, screen):
        camera_y = float(self.config.get('camera_y', 360.0))
        # Keep the existing world, Marco and scene framing, but replace the
        # animated dog-video phone with a dedicated static credits phone.
        self.renderer.render(screen, camera_y, self.elapsed, show_phone=False)
        screen.blit(self.phone_overlay, (0, 0))
        # The phone artwork stays on the pixel canvas. Credits are drawn after
        # scaling, using the same tilted geometry at physical display resolution.
        overlay = self.game.text_renderer.overlay
        if overlay is None:
            self.credits_renderer.render(screen, self.phase, self.phase_time, self.scroll_y)
        else:
            self.credits_renderer.render(overlay, self.phase, self.phase_time,
                                         self.scroll_y, scale=self.game.text_renderer.scale)
