import pygame

from game.systems.animation import LoopingAnimation
from game.rendering.shared_stella_sky import SharedStellaSky


class MarcoPOVRenderer(SharedStellaSky):
    """Render Marco's gaze views while keeping animation presentation-only.

    River, grass/wood, city, and sky use layered Scene 02 artwork. The shooting
    star is a presentation-only random event owned by this renderer.
    """

    def __init__(self, assets, config=None, rng=None):
        super().__init__(assets, config, rng)
        self.river_background = self._require(
            assets, "scene02.river.background", "scene_02/river_background.png"
        )
        self.river_frames = self._load_frames(
            assets,
            "scene02.river.bank",
            "scene_02/river_bank_{:02d}.png",
            self.FRAME_COUNT,
        )

        self.grass_background = self._require(
            assets, "scene02.grass.background", "scene_02/grass_background.png"
        )
        self.grass_frames = self._load_frames(
            assets,
            "scene02.grass.foreground",
            "scene_02/grass_foreground_{:02d}.png",
            self.FRAME_COUNT,
        )

        self.city_background = self._require(
            assets, "scene02.city.background", "scene_02/city_background.png"
        )
        self.city_frames = self._load_frames(
            assets,
            "scene02.city.foreground",
            "scene_02/city_foreground_{:02d}.png",
            self.FRAME_COUNT,
        )

        self.river_animation = LoopingAnimation(self.river_frames, self.RIVER_FPS)
        self.grass_animation = LoopingAnimation(self.grass_frames, self.GRASS_FPS)
        self.city_animation = LoopingAnimation(self.city_frames, self.CITY_FPS)
        self.reset()

    def reset(self):
        self.river_animation.reset()
        self.grass_animation.reset()
        self.city_animation.reset()
        self.reset_shared()

    def update(self, dt, current_view=None):
        # Keep environmental loops running even when their view is hidden.
        self.river_animation.update(dt)
        self.grass_animation.update(dt)
        self.city_animation.update(dt)
        self.update_shared(
            dt,
            stella_visible=current_view == "stella",
            sky_visible=current_view == "sky",
        )

    def render(self, screen, view):
        if view == "river":
            screen.blit(self.river_background, (0, 0))
            screen.blit(self.river_animation.current_frame, (0, 0))
            return

        if view == "grass":
            screen.blit(self.grass_background, (0, 0))
            screen.blit(self.grass_animation.current_frame, (0, 0))
            return

        if view == "city":
            screen.blit(self.city_background, (0, 0))
            screen.blit(self.city_animation.current_frame, (0, 0))
            return

        if view == "stella":
            # Required compositing order:
            # background -> environmental foreground -> Stella.
            screen.blit(self.stella_background, (0, 0))
            screen.blit(self.stella_foreground_animation.current_frame, (0, 0))
            if self.stella_turn_active:
                character_frame = self.stella_turn_frames[self.stella_turn_frame]
            else:
                character_frame = self.stella_idle_animation.current_frame

            # Scale the complete transparent Stella layer, preserving the same
            # ground-contact anchor for both idle and turning animations.
            scale = self.stella_character_scale
            width, height = character_frame.get_size()
            character_frame = pygame.transform.smoothscale(
                character_frame,
                (round(width * scale), round(height * scale)),
            )
            anchor_x, anchor_y = 450, 300
            offset_x, offset_y = self.stella_character_offset
            screen.blit(
                character_frame,
                (
                    round(anchor_x * (1 - scale)) + offset_x,
                    round(anchor_y * (1 - scale)) + offset_y,
                ),
            )
            return

        if view == "sky":
            # Required compositing order:
            # background -> star/moon foreground -> shooting star.
            screen.blit(self.sky_background, (0, 0))
            screen.blit(self.sky_animation.current_frame, (0, 0))

            if self.shooting_star_active:
                # The current shooting-star PNGs are cropped 54x40 frames,
                # not the older 320x247 animation canvas. Keep a fixed origin
                # for the full sequence so the authored motion stays intact.
                # The spawn point represents the visible meteor near its head.
                screen.blit(
                    self.shooting_star_frames[self.shooting_star_frame],
                    (self.shooting_star_pos[0] - 40,
                     self.shooting_star_pos[1] - 25),
                )
            return

        raise ValueError(f"Unsupported Marco POV view: {view!r}")
