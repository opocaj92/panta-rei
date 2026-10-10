import pygame
from .config import ASSETS_DIR, FPS, WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH
from .asset_manager import AssetManager
from .audio_manager import AudioManager
from .typography import Typography
from .dialogue_manager import DialogueManager
from .input_manager import InputManager
from .scene_manager import SceneManager
from .transition_manager import TransitionManager
from game.rendering.text_renderer import TextRenderer
from .localization import detect_language

class Game:
    """Compose shared services and run the single Pygame update/render loop."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        icon_path = ASSETS_DIR / "icons" / "panta_rei_64.png"
        if icon_path.is_file():
            pygame.display.set_icon(pygame.image.load(str(icon_path)))
        # Scene logic stays at 640x360; only glyphs use physical display pixels.
        self.screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.display = None
        self.viewport = pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.scale = 1.0
        self._set_display(True)
        self.fullscreen = True
        self.clock = pygame.time.Clock()

        self.input = InputManager()
        self.assets = AssetManager()
        self.audio = AudioManager()
        self.language = detect_language()
        self.dialogue = DialogueManager(language=self.language)
        self.typography = Typography(self.assets)
        self.text_renderer = TextRenderer(self.assets, typography=self.typography)
        self.transitions = TransitionManager()
        self.scenes = SceneManager(self)
        self.running = True

    def _set_display(self, fullscreen):
        if fullscreen:
            self.display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self._update_viewport()

    def _update_viewport(self):
        w, h = self.display.get_size()
        self.scale = min(w / WINDOW_WIDTH, h / WINDOW_HEIGHT)
        vw, vh = round(WINDOW_WIDTH * self.scale), round(WINDOW_HEIGHT * self.scale)
        self.viewport = pygame.Rect((w - vw) // 2, (h - vh) // 2, vw, vh)

    def logical_mouse(self, position):
        x = (position[0] - self.viewport.x) / self.scale
        y = (position[1] - self.viewport.y) / self.scale
        return (max(0, min(WINDOW_WIDTH - 1, round(x))),
                max(0, min(WINDOW_HEIGHT - 1, round(y))))

    def update_cursor_visibility(self):
        """Show the system pointer only for scenes requiring direct mouse dragging.

        Scene 05 uses its own animated pointing hand instead of the OS cursor.
        """
        pygame.mouse.set_visible(
            self.scenes.current_name in {"scene_08", "scene_09", "scene_10"}
        )

    def run(self, start_scene="scene_01", start_state=None):
        self.scenes.change_scene(start_scene, state=start_state)

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.input.begin_frame()
            self.input.mouse_position = self.logical_mouse(pygame.mouse.get_pos())

            # Raw events are offered to both the frame-level input tracker and
            # the active scene; this preserves event-sensitive scene mechanics.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.fullscreen = not self.fullscreen
                    self._set_display(self.fullscreen)
                    self.update_cursor_visibility()
                    continue  # Escape only changes display mode, not scene input.
                if event.type == pygame.WINDOWMAXIMIZED and not self.fullscreen:
                    # Treat the native maximize button as a request for true fullscreen.
                    self.fullscreen = True
                    self._set_display(True)
                    self.update_cursor_visibility()
                    continue
                if event.type in (pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED):
                    # Keep the 640x360 canvas letterboxed if the OS resizes the window.
                    if not self.fullscreen:
                        self._update_viewport()
                    continue
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                    fields = {'pos': self.logical_mouse(event.pos)}
                    if event.type == pygame.MOUSEMOTION:
                        fields['rel'] = (round(event.rel[0] / self.scale), round(event.rel[1] / self.scale))
                        fields['buttons'] = event.buttons
                    else:
                        fields['button'] = event.button
                    event = pygame.event.Event(event.type, fields)
                self.input.handle_event(event)

                # Use the same dialogue keys everywhere, but never advance
                # lines a scene has not yet made available to the player.
                if (
                    event.type == pygame.KEYDOWN
                    and event.key in (pygame.K_RETURN, pygame.K_BACKSPACE)
                ):
                    scene = self.scenes.current
                    if scene is not None and scene.allows_dialogue_advance():
                        self.dialogue.advance()

                active_before = self.scenes.current
                self.scenes.handle_input(event)
                if self.scenes.current is not active_before:
                    break  # Do not dispatch buffered events to the newly entered scene.

            self.scenes.update(dt)
            self.transitions.update(dt)

            self.text_renderer.begin_frame(self.viewport.size, self.scale)
            self.screen.fill((0, 0, 0))
            self.scenes.render(self.screen)
            self.transitions.render(self.screen)
            self.display.fill((0, 0, 0))
            self.display.blit(pygame.transform.scale(self.screen, self.viewport.size), self.viewport)
            # Overlay glyphs are already rasterized at physical resolution.
            text = self.text_renderer.overlay
            if self.transitions.alpha > 0:
                text.set_alpha(255 - self.transitions.alpha)
            self.display.blit(text, self.viewport.topleft,
                              area=pygame.Rect(0, 0, self.viewport.width, self.viewport.height))
            self.text_renderer.overlay = None
            pygame.display.flip()

        self.audio.shutdown()
        pygame.quit()
