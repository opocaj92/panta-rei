import random

import pygame

from game.rendering.animation_renderer import LoopingAnimation
from game.rendering.renderer import PrototypeRenderer


class Scene02Renderer:
    """Render Marco's gaze views while keeping animation presentation-only.

    River, grass/wood, city, and sky use layered Scene 02 artwork. The shooting
    star is a presentation-only random event owned by this renderer.
    """

    FRAME_COUNT = 4
    RIVER_FPS = 1.25
    GRASS_FPS = 1.50
    CITY_FPS = 1.00
    SKY_FPS = 0.85
    STELLA_FOREGROUND_FPS = 1.40
    STELLA_IDLE_FRAME_COUNT = 8
    STELLA_IDLE_FPS = 3.5
    STELLA_CHARACTER_SCALE = 0.82
    STELLA_CHARACTER_OFFSET = (12, -8)  # scene-authored sprite offset
    STELLA_TURN_FRAME_COUNT = 8
    STELLA_TURN_FPS = 5.0
    STELLA_TURN_MIN_DELAY = 7.0
    STELLA_TURN_MAX_DELAY = 15.0

    SHOOTING_STAR_FRAME_COUNT = 12
    SHOOTING_STAR_FPS = 12.0
    SHOOTING_STAR_MIN_DELAY = 2.0
    SHOOTING_STAR_MAX_DELAY = 4.0

    # Spawn coordinates refer to the VISIBLE meteor, not its 320x247 sprite canvas.
    SHOOTING_STAR_SPAWN_X = (55, 260)
    SHOOTING_STAR_SPAWN_Y = (0, 8)

    def __init__(self, assets, config=None, rng=None):
        self.prototype = PrototypeRenderer()
        self.rng = rng or random.Random()
        presentation = (config or {}).get("presentation", {})
        stella_placement = presentation.get("stella_placement", {})
        self.stella_character_scale = float(stella_placement.get("scale", self.STELLA_CHARACTER_SCALE))
        self.stella_character_offset = tuple(stella_placement.get("offset", self.STELLA_CHARACTER_OFFSET))
        shooting_star = presentation.get("shooting_star", {})
        self.shooting_star_fps = float(
            shooting_star.get("fps", self.SHOOTING_STAR_FPS)
        )
        self.shooting_star_min_delay = float(
            shooting_star.get("min_delay", self.SHOOTING_STAR_MIN_DELAY)
        )
        self.shooting_star_max_delay = float(
            shooting_star.get("max_delay", self.SHOOTING_STAR_MAX_DELAY)
        )
        bounds = shooting_star.get("spawn_bounds", {})
        self.shooting_star_spawn_x = tuple(
            bounds.get("x", self.SHOOTING_STAR_SPAWN_X)
        )
        self.shooting_star_spawn_y = tuple(
            bounds.get("y", self.SHOOTING_STAR_SPAWN_Y)
        )
        self.shooting_star_pos = self._next_shooting_star_position()

        stella_turn = presentation.get("stella_turn", {})
        self.stella_turn_fps = float(
            stella_turn.get("fps", self.STELLA_TURN_FPS)
        )
        self.stella_turn_min_delay = float(
            stella_turn.get("min_delay", self.STELLA_TURN_MIN_DELAY)
        )
        self.stella_turn_max_delay = float(
            stella_turn.get("max_delay", self.STELLA_TURN_MAX_DELAY)
        )

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

        self.sky_background = self._require(
            assets, "scene02.sky.background", "scene_02/sky_background.png"
        )
        self.sky_frames = self._load_frames(
            assets,
            "scene02.sky.foreground",
            "scene_02/sky_foreground_{:02d}.png",
            self.FRAME_COUNT,
        )
        self.shooting_star_frames = self._load_frames(
            assets,
            "scene02.sky.shooting_star",
            "scene_02/shooting_star_{:02d}.png",
            self.SHOOTING_STAR_FRAME_COUNT,
        )

        self.stella_background = self._require(
            assets, "scene02.stella.background", "scene_02/stella_background.png"
        )
        self.stella_foreground_frames = self._load_frames(
            assets,
            "scene02.stella.foreground",
            "scene_02/stella_foreground_{:02d}.png",
            self.FRAME_COUNT,
        )
        self.stella_idle_frames = self._load_frames(
            assets,
            "scene02.stella.idle",
            "scene_02/stella_idle_{:02d}.png",
            self.STELLA_IDLE_FRAME_COUNT,
        )
        self.stella_turn_frames = self._load_frames(
            assets,
            "scene02.stella.turning",
            "scene_02/stella_turning_{:02d}.png",
            self.STELLA_TURN_FRAME_COUNT,
        )

        self.river_animation = LoopingAnimation(self.river_frames, self.RIVER_FPS)
        self.grass_animation = LoopingAnimation(self.grass_frames, self.GRASS_FPS)
        self.city_animation = LoopingAnimation(self.city_frames, self.CITY_FPS)
        self.sky_animation = LoopingAnimation(self.sky_frames, self.SKY_FPS)
        self.stella_foreground_animation = LoopingAnimation(
            self.stella_foreground_frames, self.STELLA_FOREGROUND_FPS
        )
        self.stella_idle_animation = LoopingAnimation(
            self.stella_idle_frames, self.STELLA_IDLE_FPS
        )
        self.reset()

    @staticmethod
    def _require(assets, key, path):
        image = assets.image(key, path)
        if image is None:
            raise FileNotFoundError(f"Missing Scene 02 asset: assets/{path}")
        return image

    def _load_frames(self, assets, key_prefix, path_pattern, frame_count):
        return [
            self._require(
                assets,
                f"{key_prefix}.{index}",
                path_pattern.format(index),
            )
            for index in range(1, frame_count + 1)
        ]

    def _next_shooting_star_position(self):
        return (
            self.rng.randint(*self.shooting_star_spawn_x),
            self.rng.randint(*self.shooting_star_spawn_y),
        )

    def _next_shooting_star_delay(self):
        return self.rng.uniform(
            self.shooting_star_min_delay,
            self.shooting_star_max_delay,
        )

    def _next_stella_turn_delay(self):
        return self.rng.uniform(
            self.stella_turn_min_delay,
            self.stella_turn_max_delay,
        )

    def _update_stella_turn(self, dt, stella_visible):
        # Stella's look-at-Marco animation is a one-shot presentation event.
        # It can start only while her view is visible; once started it completes
        # before returning to the looping idle animation.
        if not self.stella_turn_active:
            if not stella_visible:
                return

            self.stella_turn_delay -= dt
            if self.stella_turn_delay > 0.0:
                return

            self.stella_turn_active = True
            self.stella_turn_frame = 0
            self.stella_turn_time = 0.0
            return

        self.stella_turn_time += dt
        frame_duration = 1.0 / self.stella_turn_fps
        while self.stella_turn_time >= frame_duration:
            self.stella_turn_time -= frame_duration
            self.stella_turn_frame += 1

            if self.stella_turn_frame >= len(self.stella_turn_frames):
                self.stella_turn_active = False
                self.stella_turn_frame = 0
                self.stella_turn_time = 0.0
                self.stella_turn_delay = self._next_stella_turn_delay()
                break

    def reset(self):
        self.river_animation.reset()
        self.grass_animation.reset()
        self.city_animation.reset()
        self.sky_animation.reset()
        self.stella_foreground_animation.reset()
        self.stella_idle_animation.reset()
        self.stella_turn_active = False
        self.stella_turn_frame = 0
        self.stella_turn_time = 0.0
        self.stella_turn_delay = self._next_stella_turn_delay()

        self.shooting_star_active = False
        self.shooting_star_time = 0.0
        self.shooting_star_frame = 0
        self.shooting_star_delay = self._next_shooting_star_delay()

    def _update_shooting_star(self, dt, sky_visible):
        # A shooting star may only begin while the player is actually looking
        # at the sky. Once it begins, however, its one-shot sequence always
        # runs to completion even if Marco looks away in the meantime.
        if not self.shooting_star_active:
            if not sky_visible:
                return

            self.shooting_star_delay -= dt
            if self.shooting_star_delay > 0.0:
                return

            self.shooting_star_pos = self._next_shooting_star_position()
            self.shooting_star_active = True
            self.shooting_star_time = 0.0
            self.shooting_star_frame = 0
            return

        self.shooting_star_time += dt
        frame_duration = 1.0 / self.shooting_star_fps

        while (
            self.shooting_star_time >= frame_duration
            and self.shooting_star_active
        ):
            self.shooting_star_time -= frame_duration
            self.shooting_star_frame += 1

            if self.shooting_star_frame >= len(self.shooting_star_frames):
                self.shooting_star_active = False
                self.shooting_star_frame = 0
                self.shooting_star_time = 0.0
                self.shooting_star_delay = self._next_shooting_star_delay()

    def update(self, dt, current_view=None):
        # Environmental loops keep running even while Marco looks elsewhere.
        # Returning to a view therefore does not restart its animation.
        self.river_animation.update(dt)
        self.grass_animation.update(dt)
        self.city_animation.update(dt)
        self.sky_animation.update(dt)
        self.stella_foreground_animation.update(dt)
        self.stella_idle_animation.update(dt)
        self._update_stella_turn(dt, current_view == "stella")

        self._update_shooting_star(dt, current_view == "sky")

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

        self.prototype.background(screen, view)
