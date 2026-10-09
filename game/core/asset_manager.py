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
        self._image_specs = {}
        self._font_specs = {}

    def image(self, key, relative_path=None, alpha=True, *, required=False):
        relative_path = relative_path or key
        spec = (str(relative_path), bool(alpha))
        if key in self._image_specs and self._image_specs[key] != spec:
            raise ValueError(f"Image key {key!r} reused with conflicting path or alpha setting")
        self._image_specs[key] = spec
        if key in self.images:
            return self.images[key]

        path = ASSETS_DIR / relative_path

        if not path.exists():
            if required:
                raise FileNotFoundError(f"Required image {key!r} not found: {path}")
            return None

        image = pygame.image.load(path)
        image = image.convert_alpha() if alpha else image.convert()
        self.images[key] = image
        return image

    def font(self, key, relative_path=None, size=24, *, required=False):
        cache_key = (key, size)
        relative_path = relative_path or key
        spec = str(relative_path)
        if cache_key in self._font_specs and self._font_specs[cache_key] != spec:
            raise ValueError(f"Font key {key!r} at size {size} reused with a different path")
        if cache_key in self.fonts:
            return self.fonts[cache_key]

        path = ASSETS_DIR / relative_path
        if required and not path.exists():
            raise FileNotFoundError(f"Required font {key!r} not found: {path}")
        font = pygame.font.Font(str(path), size) if path.exists() else pygame.font.Font(None, size)
        self._font_specs[cache_key] = spec
        self.fonts[cache_key] = font
        return font
