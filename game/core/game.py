import pygame
import os
from game.systems.touch_gestures import TouchGestures
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
        self.scaled_surface = None
        self._set_display(True)
        self.fullscreen = True
        self.clock = pygame.time.Clock()

        self.touch_enabled = os.environ.get("PANTA_REI_TOUCH", "").lower() in ("1", "true", "yes") or os.environ.get("ANDROID_ARGUMENT") is not None
        self.android_rendering = os.environ.get("ANDROID_ARGUMENT") is not None
        self.input = InputManager()
        self.touch = TouchGestures(self)
        self.assets = AssetManager()
        self.audio = AudioManager()
        self.language = detect_language()
        self.dialogue = DialogueManager(language=self.language)
        self.typography = Typography(self.assets)
        self.text_renderer = TextRenderer(self.assets, typography=self.typography)
        self.transitions = TransitionManager()
        self.scenes = SceneManager(self)
        self.running = True
        self._scene_clock_reset_requested = False
        self.preloaded_scene10_renderer = None

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
        # Reuse the output-sized scaling target until the viewport changes.
        self.scaled_surface = pygame.Surface(self.viewport.size)
        # Clear letterbox bars once; the viewport is fully repainted each frame.
        self.display.fill((0, 0, 0))

    def logical_mouse(self, position):
        x = (position[0] - self.viewport.x) / self.scale
        y = (position[1] - self.viewport.y) / self.scale
        return (max(0, min(WINDOW_WIDTH - 1, round(x))),
                max(0, min(WINDOW_HEIGHT - 1, round(y))))

    def update_cursor_visibility(self):
        """Show the desktop pointer for the main menu and drag interactions.

        Scene 05 uses its own animated pointing hand instead of the OS cursor.
        """
        pygame.mouse.set_visible(
            not self.touch_enabled and (
                self.scenes.current_name in {"scene_08", "scene_09", "scene_10"}
                or (
                    self.scenes.current_name == "scene_01"
                    and getattr(self.scenes.current, "state", None) in {"menu", "commands"}
                )
            )
        )

    def _present_frame(self):
        self.text_renderer.begin_frame(self.viewport.size, self.scale, native_text=self.android_rendering)
        self.screen.fill((0, 0, 0))
        self.scenes.render(self.screen)
        self.transitions.render(self.screen)
        pygame.transform.scale(self.screen, self.viewport.size, self.scaled_surface)
        self.display.blit(self.scaled_surface, self.viewport)
        # Desktop retains sharp display-resolution glyphs; Android draws
        # native-resolution text onto the scene before scaling.
        text = self.text_renderer.overlay
        if text is not None:
            if self.transitions.alpha > 0:
                text.set_alpha(255 - self.transitions.alpha)
            self.display.blit(text, self.viewport.topleft,
                              area=pygame.Rect(0, 0, self.viewport.width, self.viewport.height))
            self.text_renderer.overlay = None
        pygame.display.flip()

    def restart_from_credits(self, *, fade_in_duration=1.5):
        """Start a genuinely new playthrough after the final black hold.

        Each scene is constructed on activation, so discarding shared transient
        input/dialogue and renderer state prevents the previous run leaking in.
        Keep the outgoing fade opaque until the new scene is ready to render.
        """
        self.touch.cancel()
        self.input.keys_pressed.clear()
        self.input.keys_released.clear()
        self.dialogue = DialogueManager(language=self.language)
        self.preloaded_scene10_renderer = None
        self.scenes._activate_scene("scene_01", start_transition_in=False)
        self.transitions.fade_from_black(fade_in_duration)

    def run(self, start_scene="scene_01", start_state=None):
        self.scenes.change_scene(start_scene, state=start_state)

        # Present the opening scene at its initial state before any timed updates.
        self._present_frame()
        # Exclude initialization and first-frame rendering from the first dt.
        self.clock.tick()

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.input.begin_frame()
            self.input.mouse_position = self.logical_mouse(pygame.mouse.get_pos())

            # Raw events are offered to both the frame-level input tracker and
            # the active scene; this preserves event-sensitive scene mechanics.
            for raw_event in pygame.event.get():
                # SDL may also synthesize mouse events for touch. Never dispatch both.
                if self.touch_enabled and raw_event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
                    events, tapped, pan = self.touch.handle(raw_event)
                    if pan != (0, 0) and self.scenes.current_name == "scene_04":
                        self.scenes.current.pan_touch(*pan)
                    if tapped and self.scenes.current is not None and self.scenes.current.allows_dialogue_advance():
                        self.dialogue.advance()
                elif self.touch_enabled and raw_event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    # On Android mouse events are normally emulated from fingers.
                    continue
                else:
                    events = [raw_event]
                for event in events:
                    from_touch = event is not raw_event
                    if event.type == pygame.QUIT:
                        self.running = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.touch_enabled:
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
                    if not from_touch and event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
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
                        and event.key in (pygame.K_RETURN, pygame.K_SPACE)
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

            self._present_frame()
            if self._scene_clock_reset_requested:
                # Do not charge synchronous scene activation/first rendering
                # against the new scene's next gameplay/help update.
                self.clock.tick()
                self._scene_clock_reset_requested = False

        self.audio.shutdown()
        pygame.quit()
