import pygame

from game.core.scene import Scene
from game.rendering.stella_pov_renderer import StellaPOVRenderer


class Scene12(Scene):
    """Final credits, displayed inside Stella's phone."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = StellaPOVRenderer()
        self.elapsed = 0.0
        self.scroll_y = 0.0
        self.finished_scrolling = False
        self.hold_elapsed = 0.0
        self.fade_started = False
        self.terminal_black = False
        self.credit_surfaces = []

    def enter(self):
        self.elapsed = 0.0
        self.scroll_y = float(self.config.get("credits_start_y", 300.0))
        self.finished_scrolling = False
        self.hold_elapsed = 0.0
        self.fade_started = False
        self.terminal_black = False
        self._build_credits()

    def handle_input(self, event):
        # Credits are intentionally non-interactive.
        return

    def _font(self, size, italic=False):
        font = self.game.assets.font(f"credits_{size}_{italic}", size=int(size))
        font.set_italic(italic)
        return font

    def _build_credits(self):
        entries = self.config.get("credits_by_language", {}).get(getattr(self.game, "language", "en"), [])
        self.credit_surfaces = []
        for entry in entries:
            kind = entry.get("kind", "role")
            text = entry.get("text", "")
            if kind == "title":
                font = self._font(32)
                gap_after = 42
            elif kind == "name":
                font = self._font(23)
                gap_after = 34
            elif kind == "assistance":
                font = self._font(15, italic=True)
                gap_after = 5 if text.endswith(":") else 28
            else:
                font = self._font(17)
                gap_after = 10
            surf = font.render(text, True, (242, 242, 238))
            self.credit_surfaces.append((surf, gap_after))

    def update(self, dt):
        self.elapsed += dt

        if self.terminal_black:
            return

        if not self.finished_scrolling:
            self.scroll_y -= float(self.config.get("scroll_speed", 28.0)) * dt
            total_height = sum(s.get_height() + gap for s, gap in self.credit_surfaces)
            final_y = float(self.config.get("final_credit_y", 112.0))
            if self.scroll_y + total_height <= final_y:
                self.scroll_y = final_y - total_height
                self.finished_scrolling = True
            return

        if not self.fade_started:
            self.hold_elapsed += dt
            if self.hold_elapsed >= float(self.config.get("final_hold_duration", 2.0)):
                self.fade_started = True
                transition = self.config.get("transition_out", {})
                self.game.transitions.fade_to_black(
                    float(transition.get("duration", 1.5)),
                    on_complete=self._finish,
                )

    def _finish(self):
        # There is deliberately no next scene. TransitionManager remains fully
        # black and this scene stops advancing forever.
        self.terminal_black = True

    def render(self, screen):
        camera_y = float(self.config.get("camera_y", 600.0))
        self.renderer.render(screen, camera_y, self.elapsed, animate_phone=False)

        # Same phone display rectangle used by StellaPOVRenderer at the Scene 07
        # starting camera. Credits are clipped to the glass and cannot spill out.
        phone_rect = self.renderer.phone_screen_rect(screen, camera_y)
        pygame.draw.rect(screen, (26, 29, 36), phone_rect, border_radius=15)

        clip = screen.get_clip()
        screen.set_clip(phone_rect)
        y = phone_rect.top + self.scroll_y
        for surface, gap_after in self.credit_surfaces:
            x = phone_rect.centerx - surface.get_width() // 2
            screen.blit(surface, (x, int(y)))
            y += surface.get_height() + gap_after
        screen.set_clip(clip)
