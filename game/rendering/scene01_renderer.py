import pygame


class Scene01Renderer:
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

        self.water_time = 0.0
        self.water_frame = 0
        self.foreground_time = 0.0
        self.foreground_frame = 0
        self.marco_time = 0.0
        self.marco_frame = 0
        self.stella_time = 0.37
        self.stella_frame = 1

    @staticmethod
    def _require(assets, key, path, alpha=True):
        image = assets.image(key, path, alpha=alpha)
        if image is None:
            raise FileNotFoundError(f"Missing Scene 01 asset: assets/{path}")
        return image

    def reset(self):
        """Restart all looping presentation animation when Scene 01 is entered."""
        self.water_time = 0.0
        self.water_frame = 0
        self.foreground_time = 0.0
        self.foreground_frame = 0
        self.marco_time = 0.0
        self.marco_frame = 0
        self.stella_time = 0.37
        self.stella_frame = 1

    @staticmethod
    def _advance_loop(elapsed, frame, dt, fps, frame_count):
        elapsed += dt
        frame_duration = 1.0 / fps
        while elapsed >= frame_duration:
            elapsed -= frame_duration
            frame = (frame + 1) % frame_count
        return elapsed, frame

    def update(self, dt):
        """Advance the independent environmental and character idle loops."""
        self.water_time, self.water_frame = self._advance_loop(
            self.water_time,
            self.water_frame,
            dt,
            self.WATER_FPS,
            len(self.water_frames),
        )
        self.foreground_time, self.foreground_frame = self._advance_loop(
            self.foreground_time,
            self.foreground_frame,
            dt,
            self.FOREGROUND_FPS,
            len(self.foreground_frames),
        )
        self.marco_time, self.marco_frame = self._advance_loop(
            self.marco_time,
            self.marco_frame,
            dt,
            self.MARCO_FPS,
            len(self.marco_frames),
        )
        self.stella_time, self.stella_frame = self._advance_loop(
            self.stella_time,
            self.stella_frame,
            dt,
            self.STELLA_FPS,
            len(self.stella_frames),
        )

    def render(self, screen, title_alpha=0):
        screen.blit(self.background, (0, 0))
        screen.blit(self.water_frames[self.water_frame], (0, 0))
        screen.blit(self.foreground_frames[self.foreground_frame], (0, 0))
        screen.blit(self.marco_frames[self.marco_frame], self.MARCO_POS)
        screen.blit(self.stella_frames[self.stella_frame], self.STELLA_POS)

        if title_alpha > 0:
            # Copy so per-frame opacity never mutates AssetManager's cached image.
            title = self.title.copy()
            title.set_alpha(max(0, min(255, int(title_alpha))))
            title_rect = title.get_rect(
                centerx=screen.get_width() // 2,
                y=self.TITLE_Y,
            )
            screen.blit(title, title_rect)
