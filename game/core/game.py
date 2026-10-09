import pygame
from .config import FPS, WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH
from .asset_manager import AssetManager
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
        # Keep all scene coordinates at 640x360; SDL scales the output and mouse input.
        self.screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN | pygame.SCALED
        )
        self.fullscreen = True
        self.clock = pygame.time.Clock()

        self.input = InputManager()
        self.assets = AssetManager()
        self.language = detect_language()
        self.dialogue = DialogueManager(language=self.language)
        self.text_renderer = TextRenderer(self.assets)
        self.transitions = TransitionManager()
        self.scenes = SceneManager(self)
        self.running = True

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

            # Raw events are offered to both the frame-level input tracker and
            # the active scene; this preserves event-sensitive scene mechanics.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.fullscreen:
                        # Restore a normal, decorated 640x360 window.
                        self.screen = pygame.display.set_mode(
                            (WINDOW_WIDTH, WINDOW_HEIGHT),
                        )
                        self.fullscreen = False
                    else:
                        self.screen = pygame.display.set_mode(
                            (WINDOW_WIDTH, WINDOW_HEIGHT),
                            pygame.FULLSCREEN | pygame.SCALED,
                        )
                        self.fullscreen = True
                    self.update_cursor_visibility()
                    continue  # Escape only changes display mode, not scene input.
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

            self.screen.fill((0, 0, 0))
            self.scenes.render(self.screen)
            self.transitions.render(self.screen)
            pygame.display.flip()

        pygame.quit()
