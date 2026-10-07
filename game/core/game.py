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
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        self.input = InputManager()
        self.assets = AssetManager()
        self.language = detect_language()
        self.dialogue = DialogueManager(language=self.language)
        self.text_renderer = TextRenderer(self.assets)
        self.transitions = TransitionManager()
        self.scenes = SceneManager(self)
        self.running = True

    def run(self):
        self.scenes.change_scene("scene_01")

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.input.begin_frame()

            # Raw events are offered to both the frame-level input tracker and
            # the active scene; this preserves event-sensitive scene mechanics.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.input.handle_event(event)

                # Dialogue progression is a global interaction: the same keys
                # reveal/advance text regardless of which scene presents it.
                if (
                    event.type == pygame.KEYDOWN
                    and event.key in (pygame.K_RETURN, pygame.K_BACKSPACE)
                ):
                    self.dialogue.advance()

                self.scenes.handle_input(event)

            self.scenes.update(dt)
            self.transitions.update(dt)

            self.screen.fill((0, 0, 0))
            self.scenes.render(self.screen)
            self.transitions.render(self.screen)
            pygame.display.flip()

        pygame.quit()
