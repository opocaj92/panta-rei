import math
import pygame

from game.core.scene import Scene
from game.rendering.stella_pov_renderer import StellaPOVRenderer


class Scene12(Scene):
    """Final credits, on Stella's straight, black-screen phone."""

    # Pixel coordinates in the 640x360 phone overlay. Inset from the bezel
    # and camera notch; no text is ever rendered across the rounded edges.
    GLASS = pygame.Rect(261, 49, 119, 231)

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = StellaPOVRenderer(config, game.assets)
        self.phone_overlay = game.assets.image('scene_12/phone_credits', 'scene_12/phone_credits.png', required=True)
        self.elapsed = 0.0
        self.phase = 'title'
        self.phase_time = 0.0
        self.scroll_y = 0.0
        self.credit_surfaces = []
        self.credit_height = 0
        self.fade_started = False
        self.terminal_black = False
        self._build_credits()

    def enter(self):
        self.elapsed = 0.0
        self.phase = 'title'
        self.phase_time = 0.0
        self.scroll_y = float(self.GLASS.height + 8)
        self.fade_started = False
        self.terminal_black = False
        self._build_credits()

    def handle_input(self, event):
        return

    def _font(self, size, italic=False):
        font = self.game.assets.font(f'credits_12_{size}_{italic}', size=int(size))
        font.set_italic(italic)
        return font

    @staticmethod
    def _outlined_text(font, label, color, outline=(8, 13, 25), radius=1):
        """Render crisp text with a dark one-pixel outline on a transparent surface."""
        glyph = font.render(label, True, color).convert_alpha()
        edge = font.render(label, True, outline).convert_alpha()
        result = pygame.Surface(
            (glyph.get_width() + radius * 2, glyph.get_height() + radius * 2),
            pygame.SRCALPHA,
        )
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx or dy:
                    result.blit(edge, (radius + dx, radius + dy))
        result.blit(glyph, (radius, radius))
        return result

    def _build_credits(self):
        language = getattr(self.game, 'language', 'en')
        entries = self.config.get('credits_by_language', {}).get(language)
        if entries is None:
            entries = self.config.get('credits_by_language', {}).get('en', [])
        self.credit_surfaces = []
        total = 0
        for entry in entries:
            kind, label = entry['kind'], entry['text']
            if kind == 'role':
                font, color, gap = self._font(9), (158, 170, 184), 5
            elif kind == 'name':
                font, color, gap = self._font(12), (244, 241, 232), 26
            else:
                font, color, gap = self._font(10, True), (195, 201, 213), 26
            surf = self._outlined_text(font, label, color)
            # Guard against clipping long names on the narrow screen.
            if surf.get_width() > self.GLASS.width - 10:
                scale = (self.GLASS.width - 10) / surf.get_width()
                surf = pygame.transform.smoothscale(surf, (self.GLASS.width - 10, max(1, round(surf.get_height() * scale))))
            self.credit_surfaces.append((surf, gap))
            total += surf.get_height() + gap
        self.credit_height = total

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
            if self.scroll_y + self.credit_height <= -12:
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

    def _draw_centered(self, screen, surface, y):
        screen.blit(surface, (self.GLASS.centerx - surface.get_width() // 2, round(y)))

    def render(self, screen):
        camera_y = float(self.config.get('camera_y', 360.0))
        # Keep the existing world, Marco and scene framing, but replace the
        # animated dog-video phone with a dedicated static credits phone.
        self.renderer.render(screen, camera_y, self.elapsed, show_phone=False)
        screen.blit(self.phone_overlay, (0, 0))
        old_clip = screen.get_clip()
        screen.set_clip(self.GLASS)
        if self.phase in ('title', 'final'):
            title = self._outlined_text(self._font(18), 'PANTA REI', (246, 241, 228))
            subtitle = self._outlined_text(self._font(10, True), 'A game by Jacopo Castellini', (180, 194, 209))
            if subtitle.get_width() > self.GLASS.width - 8:
                subtitle = pygame.transform.smoothscale(subtitle, (self.GLASS.width - 8, subtitle.get_height()))
            # Fade in on opening, fade in again on final title.
            alpha = min(255, int(255 * min(1.0, self.phase_time / 0.7)))
            title.set_alpha(alpha)
            subtitle.set_alpha(alpha)
            self._draw_centered(screen, title, self.GLASS.centery - 21)
            self._draw_centered(screen, subtitle, self.GLASS.centery + 8)
        else:
            y = self.GLASS.top + self.scroll_y
            for surf, gap in self.credit_surfaces:
                self._draw_centered(screen, surf, y)
                y += surf.get_height() + gap
        screen.set_clip(old_clip)
