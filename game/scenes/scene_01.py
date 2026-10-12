"""Opening title and interactive main menu for desktop and touch devices."""

import pygame

from game.core.scene import Scene
from game.rendering.opening_sky_renderer import OpeningSkyRenderer


class Scene01(Scene):
    """Play the opening once, then offer Start Game and localized commands."""

    INTRO = "intro"
    MENU = "menu"
    COMMANDS = "commands"
    STARTING = "starting"

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = OpeningSkyRenderer(self.game.assets)
        self.menu_config = config["menu"]
        self.buttons = {
            name: pygame.Rect(*self.menu_config["buttons"][name])
            for name in ("start", "commands")
        }
        self.commands_panel = self.menu_config["commands_panel"]
        self.back_button = pygame.Rect(*self.commands_panel["back_button"])
        self.state = self.INTRO
        self.elapsed = 0.0
        self.title_alpha = 0.0
        self.title_state = "WAITING"
        self.title_hold_timer = 0.0
        self.piano_started_at = None
        self.motif_played = False

    def enter(self):
        self.state = self.INTRO
        self.elapsed = 0.0
        self.title_alpha = 0.0
        self.title_state = "WAITING"
        self.title_hold_timer = 0.0
        self.piano_started_at = None
        self.motif_played = False
        self.renderer.reset()
        # Commands are loaded only when requested, not at startup.
        self.game.dialogue.lines = []
        self.game.dialogue.finished = True

    def allows_dialogue_advance(self):
        # Commands are a static panel, not part of the dialogue progression.
        return False

    def handle_input(self, event):
        if self.state == self.COMMANDS:
            if (event.type == pygame.MOUSEBUTTONUP and event.button == 1
                    and self.back_button.collidepoint(event.pos)):
                self.state = self.MENU
                self.game.update_cursor_visibility()
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = self.MENU
                self.game.update_cursor_visibility()
            return
        if self.state != self.MENU or event.type != pygame.MOUSEBUTTONUP or event.button != 1:
            return
        if self.buttons["start"].collidepoint(event.pos):
            self.state = self.STARTING
            self.request_transition("scene_02")
        elif self.buttons["commands"].collidepoint(event.pos):
            self.state = self.COMMANDS
            self.game.update_cursor_visibility()

    def update(self, dt):
        self.renderer.update(dt)
        self.elapsed += dt
        title = self.config["title"]
        delay = float(title["delay"])
        fade_in = float(title["fade_in"])
        hold = float(title["hold"])

        if self.title_state == "WAITING" and self.elapsed >= delay:
            self.title_state = "FADING_IN"
            self.piano_started_at = self.elapsed
            self.game.audio.play_sfx("scene01_piano_sustain", volume=0.65)
        elif self.title_state == "FADING_IN":
            self.title_alpha = min(255.0, self.title_alpha + 255.0 * dt / max(fade_in, 0.001))
            if self.title_alpha >= 255.0:
                self.title_state = "HOLDING"
        elif self.title_state == "HOLDING":
            self.title_hold_timer += dt
            if self.title_hold_timer >= hold:
                self.title_state = "FINISHED"
                self.state = self.MENU
                self.game.update_cursor_visibility()
                # Keep the title visible above the interactive menu.

        if (self.piano_started_at is not None and not self.motif_played
                and self.elapsed - self.piano_started_at >= 0.5):
            self.motif_played = True
            self.game.audio.play_sfx("scene01_piano_motif", volume=0.6)


    def _render_buttons(self, screen):
        language = self.game.language if self.game.language in ("en", "it") else "en"
        labels = self.menu_config["labels"][language]
        font = self.game.text_renderer.font
        for name, rect in self.buttons.items():
            # A translucent, restrained treatment to match the dialogue panels.
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            panel.fill((0, 0, 0, 175))
            pygame.draw.rect(panel, (220, 215, 205, 195), panel.get_rect(), 1)
            screen.blit(panel, rect.topleft)
            self.game.text_renderer._text(
                screen, font, labels[name], (245, 240, 225),
                rect.centerx, rect.y + (rect.height - font.get_height()) // 2,
                center=True,
            )

    def _render_commands_panel(self, screen):
        cfg = self.commands_panel
        language = self.game.language if self.game.language in ("en", "it") else "en"
        labels = cfg["touch_labels" if self.game.touch_enabled else "labels"][language]
        font = self.game.text_renderer.font
        text = self.game.text_renderer._text
        panel_rect = pygame.Rect(*cfg["rect"])
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel.fill((0, 0, 0, 225))
        pygame.draw.rect(panel, (220, 215, 205, 210), panel.get_rect(), 1)
        screen.blit(panel, panel_rect.topleft)

        text(screen, font, labels["title"], (245, 240, 225), panel_rect.centerx, 46, center=True)
        left_x, right_x = 80, 285
        text(screen, font, labels["control"], (220, 215, 205), left_x, 87)
        text(screen, font, labels["action"], (220, 215, 205), right_x, 87)
        pygame.draw.line(screen, (145, 140, 130), (left_x, 108), (558, 108), 1)
        rows = labels["rows"]
        spacing = 30 if len(rows) == 4 else 27
        for index, (control, action) in enumerate(rows):
            y = 122 + index * spacing
            text(screen, font, control, (245, 240, 225), left_x, y)
            text(screen, font, action, (245, 240, 225), right_x, y)

        rect = self.back_button
        back = pygame.Surface(rect.size, pygame.SRCALPHA)
        back.fill((35, 35, 35, 240))
        pygame.draw.rect(back, (220, 215, 205, 210), back.get_rect(), 1)
        screen.blit(back, rect.topleft)
        text(screen, font, labels["back"], (245, 240, 225), rect.centerx,
             rect.y + (rect.height - font.get_height()) // 2, center=True)

    def render(self, screen):
        self.renderer.render(screen, title_alpha=self.title_alpha)
        if self.state == self.MENU:
            self._render_buttons(screen)
        elif self.state == self.COMMANDS:
            self._render_commands_panel(screen)
