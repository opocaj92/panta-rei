"""Scene 07/08: shared 640x720 painted environment and transparent sprites."""
import math
import pygame


class StellaPOVRenderer:
    WORLD_WIDTH = 640
    WORLD_HEIGHT = 720
    # Marco sits on the near-bank dirt path; his feet are in the lower world half.
    # Marco's default height is 245 px; both placement and size can be
    # overridden by each scene's presentation.marco configuration.
    MARCO_BREATHING_FPS = 3.2
    MARCO_HEIGHT = 245
    MARCO_LEFT = 132
    MARCO_BOTTOM = 445
    # Local coordinates in the 640x360 phone artwork; adjustable for credits.
    PHONE_GLASS_RECT = (265, 92, 110, 170)

    def __init__(self, config=None, assets=None):
        self.assets = assets
        presentation = (config or {}).get("presentation", {})
        marco = presentation.get("marco", {})
        self.marco_height = int(marco.get("height", self.MARCO_HEIGHT))
        self.marco_left = int(marco.get("left", self.MARCO_LEFT))
        self.marco_bottom = int(marco.get("bottom", self.MARCO_BOTTOM))
        self.phone_glass_rect = tuple(presentation.get("phone_glass_rect", self.PHONE_GLASS_RECT))
        self.world = self._load('scene_07/background.png', (640, 720), alpha=False)
        self.phone = [self._load(f'scene_07/stella_phone_{i:02d}.png', (640, 360)) for i in range(1, 9)]
        self.marco = [self._prepare_marco(self._load(f'scene_07/marco_breathing_{i:02d}.png', (640, 360))) for i in range(1, 5)]

    def _load(self, name, size, alpha=True):
        image = self.assets.image(name, name, alpha=alpha, required=True)
        if image.get_size() != size:
            raise ValueError(f"{name}: expected {size}, got {image.get_size()}")
        return image

    def _prepare_marco(self, source):
        # Crop the transparent margins before scaling; otherwise his actual
        # character size depends on empty pixels in the 640x360 source frame.
        bounds = source.get_bounding_rect(min_alpha=8)
        cropped = source.subsurface(bounds).copy()
        target_w = round(cropped.get_width() * self.marco_height / cropped.get_height())
        return pygame.transform.scale(cropped, (target_w, self.marco_height))

    def render(self, screen, camera_y, elapsed=0.0, zoom=1.0, animate_phone=True, focus=None):
        """Render one continuous world; sprites live at fixed WORLD coordinates.

        Marco and the phone are animated in the full 640x720 world on every
        frame, including when outside the visible camera viewport.
        """
        width, height = screen.get_size()
        zoom = max(1.0, float(zoom))
        view_w, view_h = width / zoom, height / zoom
        camera_y = max(0.0, min(float(camera_y), self.WORLD_HEIGHT - height))
        if focus is None:
            # Scene 07 retains its original centred camera movement.
            cx = self.WORLD_WIDTH / 2
            cy = camera_y + height / 2
            left = cx - view_w / 2
            top = cy - view_h / 2
        else:
            # Keep the chosen world-space point in the same screen position
            # as we zoom, making the approach naturally favour Marco.
            fx, fy = focus
            progress = 1.0 - 1.0 / zoom
            left = progress * fx
            top = camera_y + progress * fy
        left = max(0.0, min(left, self.WORLD_WIDTH - view_w))
        top = max(0.0, min(top, self.WORLD_HEIGHT - view_h))
        view = pygame.Rect(round(left), round(top), round(view_w), round(view_h))
        # Compose BOTH animations into the entire 640x720 world BEFORE
        # cropping the camera viewport. They keep playing even off-screen.
        # This also lets Marco straddle the y=360 boundary without clipping.
        world_frame = self.world.copy()
        marco_frame = self.marco[int(elapsed * self.MARCO_BREATHING_FPS) % len(self.marco)]
        # False freezes the phone on its first frame, rather than removing it.
        phone_index = int(elapsed * 5) % len(self.phone) if animate_phone else 0
        phone_frame = self.phone[phone_index]
        marco_y = self.marco_bottom - marco_frame.get_height()
        world_frame.blit(marco_frame, (self.marco_left, marco_y))
        world_frame.blit(phone_frame, (0, 360))
        # Crop only after all sprites have been composited in world space.
        frame = world_frame.subsurface(view).copy()
        if frame.get_size() != (width, height):
            frame = pygame.transform.scale(frame, (width, height))
        screen.blit(frame, (0, 0))

    def phone_screen_rect(self, screen, camera_y):
        """Phone glass bounds in viewport pixels for the unzoomed phone view.

        The phone artwork begins at world y=360; the credit scene overlays
        the glass without drawing outside its bounds.
        """
        x, y, w, h = self.phone_glass_rect
        return pygame.Rect(x, round(360 + y - float(camera_y)), w, h)
