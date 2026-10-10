"""Scene 11 panorama, reusing Marco POV animation layers."""
import random
import pygame
from game.rendering.shared_stella_sky import SharedStellaSky


class SkyPanoramaRenderer(SharedStellaSky):
    def __init__(self, assets, config):
        super().__init__(assets, config)
        self.world_background = self._require(assets, "scene11.background", "scene_11/background.png")
        if self.world_background.get_size() != (640, 720):
            raise ValueError("Scene 11 panorama must be 640x720")
        self.facing_frames = self.stella_turn_frames[2:6]  # authored 03..06, inclusive
        self.elapsed = 0.0
        self.meteors_enabled = False
        self.meteor_triggered = False
        self.reset()

    def reset(self):
        self.reset_shared()
        self.elapsed = 0.0
        self.meteors_enabled = False
        self.meteor_triggered = False

    def update(self, dt, sky_complete=False):
        self.elapsed += dt
        # Both environmental animations advance regardless of camera visibility.
        self.stella_foreground_animation.update(dt)
        self.sky_animation.update(dt)
        if sky_complete:
            self.meteors_enabled = True
        # Do not decrement the meteor spawn timer until the pan has completed.
        if self.meteors_enabled and (not self.meteor_triggered or self.shooting_star_active):
            self._update_shooting_star(dt, True)
            if self.shooting_star_active:
                self.meteor_triggered = True

    def render(self, screen, camera_y):
        world = self.world_background.copy()
        # Top: background -> animated sky. Bottom: background -> grass -> Stella.
        world.blit(self.sky_animation.current_frame, (0, 0))
        world.blit(self.stella_foreground_animation.current_frame, (0, 360))
        character = self.facing_frames[int(self.elapsed * (len(self.facing_frames) * self.STELLA_IDLE_FPS / len(self.stella_idle_frames))) % len(self.facing_frames)]
        scale = self.stella_character_scale
        w, h = character.get_size()
        character = pygame.transform.smoothscale(character, (round(w * scale), round(h * scale)))
        offset_x, offset_y = self.stella_character_offset
        world.blit(character, (round(450 * (1-scale)) + offset_x, 360 + round(300 * (1-scale)) + offset_y))
        if self.meteors_enabled and self.shooting_star_active:
            x, y = self.shooting_star_pos
            world.blit(self.shooting_star_frames[self.shooting_star_frame], (x-40, y-25))
        view_y = max(0, min(360, round(camera_y)))
        view = world.subsurface(pygame.Rect(0, view_y, 640, 360))
        if screen.get_size() != (640, 360):
            view = pygame.transform.scale(view, screen.get_size())
        screen.blit(view, (0, 0))
