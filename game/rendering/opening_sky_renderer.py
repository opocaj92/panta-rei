import pygame
from game.systems.animation import LoopingAnimation


class OpeningSkyRenderer:
    """Compose Scene 01 from complete replacement animation frames.

    Animation state is presentation-only. Water, foreground, and Marco each use
    complete frames, so no animated element is duplicated underneath a static copy.
    """

    MARCO_POS = (115, 190)
    STELLA_POS = (188, 197)
    TITLE_Y = 55

    WATER_FRAME_COUNT = 4
    WATER_FPS = 1.35

    FOREGROUND_FRAME_COUNT = 4
    FOREGROUND_FPS = 1.60

    MARCO_FRAME_COUNT = 3
    MARCO_FPS = 1.00

    STELLA_FRAME_COUNT = 3
    STELLA_FPS = 0.90

    def __init__(self, assets):
        self.background = self._require(
            assets, "scene01.background", "scene_01/background.png", alpha=False
        )

        self.water_frames = [
            self._require(
                assets,
                f"scene01.water.{index}",
                f"scene_01/water_{index:02d}.png",
            )
            for index in range(1, self.WATER_FRAME_COUNT + 1)
        ]

        self.foreground_frames = [
            self._require(
                assets,
                f"scene01.foreground.{index}",
                f"scene_01/foreground_{index:02d}.png",
            )
            for index in range(1, self.FOREGROUND_FRAME_COUNT + 1)
        ]

        self.marco_frames = [
            self._require(
                assets,
                f"scene01.marco_idle.{index}",
                f"scene_01/marco_idle_{index:02d}.png",
            )
            for index in range(1, self.MARCO_FRAME_COUNT + 1)
        ]

        self.stella_frames = [
            self._require(
                assets,
                f"scene01.stella_idle.{index}",
                f"scene_01/stella_idle_{index:02d}.png",
            )
            for index in range(1, self.STELLA_FRAME_COUNT + 1)
        ]
        self.title = self._require(
            assets, "scene01.title", "scene_01/title.png"
        )

        self.water_animation = LoopingAnimation(self.water_frames, self.WATER_FPS)
        self.foreground_animation = LoopingAnimation(self.foreground_frames, self.FOREGROUND_FPS)
        self.marco_animation = LoopingAnimation(self.marco_frames, self.MARCO_FPS)
        self.stella_animation = LoopingAnimation(self.stella_frames, self.STELLA_FPS)
        self.reset()

    @staticmethod
    def _require(assets, key, path, alpha=True):
        image = assets.image(key, path, alpha=alpha)
        if image is None:
            raise FileNotFoundError(f"Missing Scene 01 asset: assets/{path}")
        return image

    def reset(self):
        """Restart all loops, preserving Stella's authored initial phase."""
        for animation in (self.water_animation, self.foreground_animation,
                          self.marco_animation, self.stella_animation):
            animation.reset()
        self.stella_animation.elapsed = 0.37
        self.stella_animation.frame_index = 1

    def update(self, dt):
        for animation in (self.water_animation, self.foreground_animation,
                          self.marco_animation, self.stella_animation):
            animation.update(dt)

    def render(self, screen, title_alpha=0):
        screen.blit(self.background, (0, 0))
        screen.blit(self.water_animation.current_frame, (0, 0))
        screen.blit(self.foreground_animation.current_frame, (0, 0))
        screen.blit(self.marco_animation.current_frame, self.MARCO_POS)
        screen.blit(self.stella_animation.current_frame, self.STELLA_POS)

        if title_alpha > 0:
            # Copy so per-frame opacity never mutates AssetManager's cached image.
            title = self.title.copy()
            title.set_alpha(max(0, min(255, int(title_alpha))))
            title_rect = title.get_rect(
                centerx=screen.get_width() // 2,
                y=self.TITLE_Y,
            )
            screen.blit(title, title_rect)
