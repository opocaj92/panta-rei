import pygame


class TextRenderer:
    """Reusable typography/UI presentation; dialogue timing remains in DialogueManager."""

    def __init__(self, assets):
        self.font = assets.font("ui_dialogue", size=28)
        self.thought_font = assets.font("ui_thought", size=25)
        self.thought_font.set_italic(True)
        self.help_font = assets.font("ui_help", size=24)

    @staticmethod
    def _wrap(text, font, max_width):
        words = text.split(" ")
        lines = []
        current = ""

        for word in words:
            candidate = word if not current else current + " " + word
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)
        return lines

    def dialogue(self, screen, dialogue, rect=None):
        line = dialogue.current_line
        if line is None:
            return

        rect = rect or pygame.Rect(80, 455, screen.get_width() - 160, 110)
        box = pygame.Surface(rect.size, pygame.SRCALPHA)
        box.fill((0, 0, 0, 190))
        screen.blit(box, rect.topleft)

        speaker = line.get("speaker", "")
        if speaker:
            speaker_surface = self.font.render(speaker, True, (210, 210, 210))
            screen.blit(speaker_surface, (rect.x + 20, rect.y + 12))

        lines = self._wrap(dialogue.visible_text, self.font, rect.width - 40)
        for index, text in enumerate(lines):
            surface = self.font.render(text, True, (245, 245, 245))
            position = (rect.x + 20, rect.y + 48 + index * self.font.get_linesize())
            screen.blit(surface, position)

    def plain(self, screen, dialogue, position="center", max_width=760):
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
            surface = self.font.render(text, True, (245, 245, 245))
            rect = surface.get_rect(
                centerx=screen.get_width() // 2,
                y=y + index * line_height,
            )
            screen.blit(surface, rect)

    def thought(self, screen, dialogue, max_width=560):
        if dialogue.current_line is None:
            return

        text = f"({dialogue.visible_text}"
        if dialogue.current_text_complete:
            text += ")"

        lines = self._wrap(text, self.thought_font, max_width)
        y = int(screen.get_height() * 0.22)
        line_height = self.thought_font.get_linesize()

        for index, text in enumerate(lines):
            surface = self.thought_font.render(text, True, (205, 205, 215))
            rect = surface.get_rect(
                centerx=screen.get_width() // 2 + 55,
                y=y + index * line_height,
            )
            screen.blit(surface, rect)

    def help(self, screen, text):
        if not text:
            return

        padding_x = 18
        padding_y = 12
        surface = self.help_font.render(text, True, (245, 245, 245))
        box = pygame.Surface(
            (surface.get_width() + 2 * padding_x, surface.get_height() + 2 * padding_y),
            pygame.SRCALPHA,
        )
        box.fill((0, 0, 0, 190))

        x = (screen.get_width() - box.get_width()) // 2
        y = screen.get_height() - box.get_height() - 24
        screen.blit(box, (x, y))
        screen.blit(surface, (x + padding_x, y + padding_y))
