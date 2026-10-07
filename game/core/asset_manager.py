import pygame
from .config import ASSETS_DIR

class AssetManager:
    """Load and cache assets by caller-supplied logical names.

    A logical key is expected to identify one asset consistently for the life of
    the game. Keeping that contract here lets renderers change physical files
    later without leaking paths into scene logic.
    """

    def __init__(self):
        self.images = {}
        self.fonts = {}

    def image(self, key, relative_path=None, alpha=True):
        if key in self.images:
            return self.images[key]

        relative_path = relative_path or key
        path = ASSETS_DIR / relative_path

        if not path.exists():
            return None

        image = pygame.image.load(path)
        image = image.convert_alpha() if alpha else image.convert()
        self.images[key] = image
        return image

    def font(self, key, relative_path=None, size=24):
        cache_key = (key, size)
        if cache_key in self.fonts:
            return self.fonts[cache_key]

        relative_path = relative_path or key
        path = ASSETS_DIR / relative_path
        font = pygame.font.Font(str(path), size) if path.exists() else pygame.font.Font(None, size)
        self.fonts[cache_key] = font
        return font
