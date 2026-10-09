"""Shared, cached font styles for both logical and high-resolution rendering."""
import json
import pygame
from game.core.config import DATA_DIR, ASSETS_DIR


class Typography:
    """Resolve authored font paths through AssetManager and cache styled sizes."""

    def __init__(self, assets):
        self.assets = assets
        with (DATA_DIR / "presentation" / "typography.json").open(encoding="utf-8") as source:
            self.styles = json.load(source)
        self._fonts = {}

    def font(self, style, scale=1.0):
        spec = self.styles[style]
        size = max(1, round(spec["size"] * float(scale)))
        italic = bool(spec.get("italic", False))
        key = (style, size, italic)
        if key not in self._fonts:
            # `path` is an asset-relative font file, never an opaque font key.
            # Missing optional fonts intentionally use Pygame's bundled default
            # at *all* display resolutions, so layout and rasterization agree.
            relative_path = spec.get("path")
            if relative_path and not (ASSETS_DIR / relative_path).is_file():
                raise FileNotFoundError(f"Typography style {style!r} references missing font: {ASSETS_DIR / relative_path}")
            font = self.assets.font(f"typography.{style}", relative_path=relative_path or f"__default__.{style}", size=size)
            font.set_italic(italic)
            self._fonts[key] = font
        return self._fonts[key]

    def scaled(self, style, scale):
        return self.font(style, scale)
