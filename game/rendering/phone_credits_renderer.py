"""Credits typography and pixel-accurate projection onto the tilted phone."""
import pygame
from game.core.typography import Typography


class PhoneCreditsRenderer:
    # Four inset corners of the visible glass in the ORIGINAL 640x360 PNG.
    # Clockwise: top-left, top-right, bottom-right, bottom-left.
    # These points stay inside the bezel and below the speaker notch.
    SCREEN_QUAD = ((256, 55), (383, 43), (397, 287), (272, 298))
    # Credits are laid out on a straight virtual screen, then projected.
    GLASS = pygame.Rect(0, 0, 119, 231)

    def __init__(self, assets, display=None, typography=None):
        self.assets = assets
        self.typography = typography or Typography(assets)
        display = display or {}
        self.screen_quad = tuple(tuple(point) for point in display.get("screen_quad", type(self).SCREEN_QUAD))
        self.glass = pygame.Rect(display.get("virtual_glass", self.GLASS))
        self.credit_surfaces = []
        self.credit_height = 0
        self._entries = []
        self._scaled_cache = {}
        self._static_cache = {}

    @staticmethod
    def outlined_text(font, label, color, outline=(8, 13, 25), radius=1):
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

    def set_credits(self, entries):
        self._entries = list(entries)
        self._scaled_cache.clear()
        credit_surfaces = []
        total = 0
        for entry in entries:
            kind, label = entry['kind'], entry['text']
            if kind == 'role':
                font, color, gap = self.typography.font("credits_role"), (158, 170, 184), 5
            elif kind == 'name':
                font, color, gap = self.typography.font("credits_name"), (244, 241, 232), 26
            else:
                font, color, gap = self.typography.font("credits_other"), (195, 201, 213), 26
            surf = self.outlined_text(font, label, color)
            # Guard against clipping long names on the narrow screen.
            if surf.get_width() > self.glass.width - 10:
                scale = (self.glass.width - 10) / surf.get_width()
                surf = pygame.transform.smoothscale(surf, (self.glass.width - 10, max(1, round(surf.get_height() * scale))))
            credit_surfaces.append((surf, gap))
            total += surf.get_height() + gap
        self.credit_surfaces = credit_surfaces
        self.credit_height = total

    def draw_centered(self, surface, glyph, y):
        surface.blit(glyph, (self.glass.centerx - glyph.get_width() // 2, round(y)))

    def project_credits(self, screen, credits, scale=1.0):
        """Map a straight credits surface onto the slanted phone glass.

        Row-wise scaling uses only Pygame, so packaged builds do not need
        OpenCV or NumPy. A quadrilateral alpha mask keeps every pixel inside
        the display, never over the bezel or hands.
        """
        tl, tr, br, bl = [tuple(round(v * scale) for v in point) for point in self.screen_quad]
        left = min(tl[0], bl[0])
        right = max(tr[0], br[0])
        top = min(tl[1], tr[1])
        bottom = max(bl[1], br[1])
        warped = pygame.Surface((right - left + 1, bottom - top + 1), pygame.SRCALPHA)
        # Project each horizontal credits row between the corresponding
        # points on the two sloping sides. The previous column-wise mapping
        # used a fixed x -> source-column relation, even though the phone's
        # horizontal boundaries shift with height. That made scrolling text
        # appear to drift sideways as it moved down the screen.
        source_height = credits.get_height()
        for src_y in range(source_height):
            v = (src_y + 0.5) / source_height
            left_x = tl[0] + v * (bl[0] - tl[0])
            right_x = tr[0] + v * (br[0] - tr[0])
            left_y = tl[1] + v * (bl[1] - tl[1])
            right_y = tr[1] + v * (br[1] - tr[1])
            width = max(1, round(right_x - left_x))
            row = credits.subsurface((0, src_y, credits.get_width(), 1))
            stretched = pygame.transform.scale(row, (width, 1))
            # Preserve the slant of the top and bottom screen edges.
            # Group nearby destination columns into short horizontal strips
            # rather than applying a fixed offset to the whole image.
            run_start = 0
            while run_start < width:
                u = (run_start + 0.5) / width
                dst_y = round(left_y + u * (right_y - left_y)) - top
                run_end = run_start + 1
                while run_end < width:
                    next_u = (run_end + 0.5) / width
                    if round(left_y + next_u * (right_y - left_y)) - top != dst_y:
                        break
                    run_end += 1
                warped.blit(stretched, (round(left_x) + run_start - left, dst_y),
                            area=pygame.Rect(run_start, 0, run_end - run_start, 1))
                run_start = run_end

        mask = pygame.Surface(warped.get_size(), pygame.SRCALPHA)
        points = [(round(x * scale) - left, round(y * scale) - top) for x, y in self.screen_quad]
        pygame.draw.polygon(mask, (255, 255, 255, 255), points)
        warped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(warped, (left, top))


    def _scaled_entries(self, scale):
        """Cache high-resolution glyphs; preserve authored logical spacing."""
        key = round(scale, 5)
        if key not in self._scaled_cache:
            items = []
            for entry in self._entries:
                kind, label = entry['kind'], entry['text']
                if kind == 'role':
                    style, color, gap = 'credits_role', (158, 170, 184), 5
                elif kind == 'name':
                    style, color, gap = 'credits_name', (244, 241, 232), 26
                else:
                    style, color, gap = 'credits_other', (195, 201, 213), 26
                glyph = self.outlined_text(self.typography.font(style, scale), label, color,
                                           radius=max(1, round(scale)))
                width = round((self.glass.width - 10) * scale)
                if glyph.get_width() > width:
                    ratio = width / glyph.get_width()
                    glyph = pygame.transform.smoothscale(glyph, (width, max(1, round(glyph.get_height() * ratio))))
                items.append((glyph, round(gap * scale)))
            self._scaled_cache[key] = items
        return self._scaled_cache[key]

    def render(self, screen, phase, phase_time, scroll_y, scale=1.0):
        """Draw the complete credits presentation; narrative timing stays in Scene 12."""
        credits = pygame.Surface((max(1, round(self.glass.width * scale)),
                                  max(1, round(self.glass.height * scale))), pygame.SRCALPHA)
        if phase in ("final", "title"):
            key = (phase, round(scale, 5))
            static = self._static_cache.get(key)
            if static is None:
                static = pygame.Surface(credits.get_size(), pygame.SRCALPHA)
                if phase == "final":
                    # The final message replaces the authorship title; the opening title stays unchanged.
                    lines = (
                        ("A special thank to", "credits_subtitle", (180, 194, 209)),
                        ("YOU", "credits_title", (246, 241, 228)),
                        ("for playing Panta Rei", "credits_subtitle", (180, 194, 209)),
                    )
                    glyphs = []
                    for label, style, color in lines:
                        glyph = self.outlined_text(self.typography.font(style, scale), label, color,
                                                   radius=max(1, round(scale)))
                        max_width = round((self.glass.width - 8) * scale)
                        if glyph.get_width() > max_width:
                            ratio = max_width / glyph.get_width()
                            glyph = pygame.transform.smoothscale(glyph,
                                (max_width, max(1, round(glyph.get_height() * ratio))))
                        glyphs.append(glyph)
                    spacing = round(8 * scale)
                    total_height = sum(g.get_height() for g in glyphs) + 2 * spacing
                    y = (credits.get_height() - total_height) // 2
                    for glyph in glyphs:
                        static.blit(glyph, ((credits.get_width() - glyph.get_width()) // 2, y))
                        y += glyph.get_height() + spacing
                elif phase == "title":
                    title = self.outlined_text(self.typography.font("credits_title", scale), "PANTA REI", (246, 241, 228), radius=max(1, round(scale)))
                    subtitle = self.outlined_text(self.typography.font("credits_subtitle", scale), "A game by Jacopo Castellini", (180, 194, 209), radius=max(1, round(scale)))
                    if subtitle.get_width() > round((self.glass.width - 8) * scale):
                        subtitle = pygame.transform.smoothscale(subtitle, (round((self.glass.width - 8) * scale), subtitle.get_height()))
                    static.blit(title, ((credits.get_width() - title.get_width()) // 2, round((self.glass.centery - 21) * scale)))
                    static.blit(subtitle, ((credits.get_width() - subtitle.get_width()) // 2, round((self.glass.centery + 8) * scale)))
                self._static_cache[key] = static
            credits.blit(static, (0, 0))
            credits.fill((255, 255, 255, min(255, int(255 * min(1.0, phase_time / 0.7)))), special_flags=pygame.BLEND_RGBA_MULT)
        else:
            y = round((self.glass.top + scroll_y) * scale)
            for surf, gap in (self.credit_surfaces if scale == 1.0 else self._scaled_entries(scale)):
                credits.blit(surf, ((credits.get_width() - surf.get_width()) // 2, round(y)))
                y += surf.get_height() + gap
        self.project_credits(screen, credits, scale=scale)
