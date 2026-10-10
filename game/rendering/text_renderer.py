import math
import pygame
from game.core.typography import Typography


class TextRenderer:
    """Reusable typography/UI presentation for the 640x360 design canvas."""

    def __init__(self, assets, typography=None):
        self.assets = assets
        self.overlay = None
        self.scale = 1.0
        self.typography = typography or Typography(assets)
        self.font = self.typography.font("dialogue")
        self.speaker_font = self.typography.font("speaker")
        self.thought_font = self.typography.font("thought")
        self.help_font = self.typography.font("help")
        self._font_styles = {id(self.font): "dialogue", id(self.speaker_font): "speaker",
                             id(self.thought_font): "thought", id(self.help_font): "help"}

    def begin_frame(self, size, scale):
        """Draw glyphs at output resolution, while boxes stay on the pixel canvas."""
        self.scale = float(scale)
        self.overlay = pygame.Surface(size, pygame.SRCALPHA)

    def _text(self, screen, font, label, color, x, y, center=False):
        if self.overlay is None:
            glyph = font.render(label, True, color)
            rect = glyph.get_rect(centerx=round(x), y=round(y)) if center else glyph.get_rect(topleft=(round(x), round(y)))
            screen.blit(glyph, rect)
            return
        # Use exactly the same font identity as the native-resolution layout.
        scale = self.scale
        style = self._font_styles[id(font)]
        high = self.typography.scaled(style, scale)
        glyph = high.render(label, True, color)
        # Align to the original glyph's ascent/height to avoid changing layout.
        if center:
            rect = glyph.get_rect(centerx=round(x * scale), y=round(y * scale))
        else:
            rect = glyph.get_rect(topleft=(round(x * scale), round(y * scale)))
        self.overlay.blit(glyph, rect)

    @staticmethod
    def _wrap(text, font, max_width):
        """Wrap by measured glyph width, including words wider than the box."""
        if not text:
            return []
        lines = []
        for paragraph in text.split("\n"):
            current = ""
            for word in paragraph.split(" "):
                candidate = word if not current else current + " " + word
                if font.size(candidate)[0] <= max_width:
                    current = candidate
                    continue
                if current:
                    lines.append(current)
                    current = ""
                # Break unusually long unspaced words rather than overflowing.
                for char in word:
                    if current and font.size(current + char)[0] > max_width:
                        lines.append(current)
                        current = ""
                    current += char
            lines.append(current)
        return lines

    def dialogue(self, screen, dialogue, rect=None):
        line = dialogue.current_line
        if line is None:
            return
        rect = pygame.Rect(rect or (51, 273, screen.get_width() - 102, 66))
        speaker = line.get("speaker", "")
        padding_x = 13
        top_padding = 7
        text_top = 29 if speaker else 10
        bottom_padding = 7
        width = max(1, rect.width - 2 * padding_x)

        # Keep the authored box's bottom edge fixed. Grow upward when a line
        # needs more rows; this also handles Italian/English length differences.
        lines = self._wrap(dialogue.visible_text, self.font, width)
        line_height = self.font.get_linesize()
        required_height = text_top + len(lines) * line_height + bottom_padding
        height = max(rect.height, required_height)
        height = min(height, rect.bottom)  # Never leave the 640x360 canvas.
        box_rect = pygame.Rect(rect.x, rect.bottom - height, rect.width, height)
        box = pygame.Surface(box_rect.size, pygame.SRCALPHA)
        box.fill((0, 0, 0, 190))
        screen.blit(box, box_rect.topleft)
        if speaker:
            self._text(screen, self.speaker_font, speaker, (225, 225, 225),
                       box_rect.x + padding_x, box_rect.y + top_padding)

        # Very long passages should still stay within the available canvas.
        # Use a clip for native and high-resolution text layers alike.
        native_clip = screen.get_clip()
        overlay_clip = self.overlay.get_clip() if self.overlay is not None else None
        text_area = pygame.Rect(box_rect.x + padding_x, box_rect.y + text_top,
                                width, max(0, box_rect.height - text_top - bottom_padding))
        screen.set_clip(text_area)
        if self.overlay is not None:
            scale = self.scale
            self.overlay.set_clip(pygame.Rect(round(text_area.x * scale), round(text_area.y * scale),
                                              round(text_area.width * scale), round(text_area.height * scale)))
        try:
            for index, text in enumerate(lines):
                y = box_rect.y + text_top + index * line_height
                if y + line_height > box_rect.bottom - bottom_padding:
                    break
                self._text(screen, self.font, text, (245, 245, 245), box_rect.x + padding_x, y)
        finally:
            screen.set_clip(native_clip)
            if self.overlay is not None:
                self.overlay.set_clip(overlay_clip)

    def plain(self, screen, dialogue, position="center", max_width=486):
        if dialogue.current_line is None:
            return
        lines = self._wrap(dialogue.visible_text, self.font, max_width)
        if not lines:
            return
        line_height = self.font.get_linesize()
        total_height = len(lines) * line_height
        if position == "center":
            y = (screen.get_height() - total_height) // 2
        elif position == "lower_center":
            y = int(screen.get_height() * 0.68)
        else:
            raise ValueError(f"Unknown plain dialogue position: {position}")
        for index, text in enumerate(lines):
            self._text(screen, self.font, text, (245, 245, 245), screen.get_width() // 2, y + index * line_height, center=True)

    def thought(self, screen, dialogue, max_width=358):
        if dialogue.current_line is None:
            return
        text = f"({dialogue.visible_text}" + (")" if dialogue.current_text_complete else "")
        lines = self._wrap(text, self.thought_font, max_width)
        y = int(screen.get_height() * 0.22)
        line_height = self.thought_font.get_linesize()
        for index, text in enumerate(lines):
            self._text(screen, self.thought_font, text, (220, 220, 230), screen.get_width() // 2 + 35, y + index * line_height, center=True)

    def help(self, screen, text):
        if not text:
            return
        padding_x, padding_y = 11, 7
        # Measure the font used for actual drawing: text is rendered onto a
        # display-resolution overlay, which may have different glyph metrics.
        if self.overlay is not None:
            display_font = self.typography.scaled("help", self.scale)
            text_width, text_height = display_font.size(text)
            text_width = math.ceil(text_width / self.scale)
            text_height = math.ceil(text_height / self.scale)
        else:
            text_width, text_height = self.help_font.size(text)
        box = pygame.Surface((text_width + 2 * padding_x, text_height + 2 * padding_y), pygame.SRCALPHA)
        box.fill((0, 0, 0, 190))
        x = (screen.get_width() - box.get_width()) // 2
        y = 14
        screen.blit(box, (x, y))
        self._text(screen, self.help_font, text, (245, 245, 245), x + padding_x, y + padding_y)
