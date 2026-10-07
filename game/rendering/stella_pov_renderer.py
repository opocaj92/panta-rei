import math
import pygame


class StellaPOVRenderer:
    """Prototype tall composition shared by Stella-POV scenes."""

    WORLD_WIDTH = 1000
    WORLD_HEIGHT = 1200
    PHONE_SCREEN_WORLD_RECT = pygame.Rect(416, 710, 168, 295)

    def __init__(self):
        self.world = pygame.Surface((self.WORLD_WIDTH, self.WORLD_HEIGHT))
        self._build_static_world()

    def _build_static_world(self):
        surface = self.world
        surface.fill((11, 19, 31))

        # Upper half: Marco isolated in Stella's attention. This deliberately
        # mirrors Scene 02's character-focused Stella view: no river or landscape
        # background competing with the person she has just looked up at.
        stars = [
            (65, 70), (145, 125), (230, 55), (315, 105), (405, 65),
            (520, 130), (620, 55), (705, 110), (815, 75), (925, 130),
        ]
        for x, y in stars:
            pygame.draw.circle(surface, (220, 220, 210), (x, y), 2)

        # Marco: character-centric prototype framing, analogous to Stella in Scene 02.
        pygame.draw.circle(surface, (205, 166, 145), (500, 255), 45)
        pygame.draw.rect(surface, (54, 58, 70), (445, 300, 110, 155), border_radius=20)
        pygame.draw.line(surface, (54, 58, 70), (470, 435), (425, 510), 24)
        pygame.draw.line(surface, (54, 58, 70), (530, 435), (575, 510), 24)

        # Lower half: Stella's lap/arms and phone dominate the starting frame.
        pygame.draw.rect(surface, (20, 31, 40), (0, 600, 1000, 600))
        pygame.draw.ellipse(surface, (74, 63, 78), (245, 880, 510, 330))
        pygame.draw.line(surface, (198, 158, 145), (385, 880), (455, 800), 30)
        pygame.draw.line(surface, (198, 158, 145), (615, 880), (545, 800), 30)

        # Phone body. The video itself is animated in render().
        pygame.draw.rect(surface, (14, 14, 18), (405, 690, 190, 340), border_radius=24)
        pygame.draw.rect(surface, (42, 45, 54), self.PHONE_SCREEN_WORLD_RECT, border_radius=15)
        pygame.draw.circle(surface, (9, 9, 11), (500, 1016), 6)


    def phone_screen_rect(self, screen, camera_y, zoom=1.0):
        """Return the phone glass rectangle in screen coordinates for this view."""
        max_y = max(0, self.WORLD_HEIGHT - screen.get_height())
        camera_y = max(0.0, min(float(camera_y), float(max_y)))
        zoom = max(1.0, float(zoom))
        view_w = screen.get_width() / zoom
        view_h = screen.get_height() / zoom
        center_x = self.WORLD_WIDTH / 2.0
        center_y = camera_y + screen.get_height() / 2.0
        left = max(0.0, min(center_x - view_w / 2.0, self.WORLD_WIDTH - view_w))
        top = max(0.0, min(center_y - view_h / 2.0, self.WORLD_HEIGHT - view_h))
        r = self.PHONE_SCREEN_WORLD_RECT
        return pygame.Rect(
            int(round((r.x - left) * zoom)), int(round((r.y - top) * zoom)),
            int(round(r.width * zoom)), int(round(r.height * zoom)),
        )

    def render(self, screen, camera_y, elapsed=0.0, zoom=1.0, animate_phone=True):
        max_y = max(0, self.WORLD_HEIGHT - screen.get_height())
        camera_y = max(0.0, min(float(camera_y), float(max_y)))

        zoom = max(1.0, float(zoom))
        view_w = screen.get_width() / zoom
        view_h = screen.get_height() / zoom
        # Keep Marco centered while Stella approaches. The clamp below is the
        # visual safety boundary: even at maximum configured zoom the viewport
        # never crosses outside the authored world or lets the POV overlap Marco.
        center_x = self.WORLD_WIDTH / 2.0
        center_y = camera_y + screen.get_height() / 2.0
        left = max(0.0, min(center_x - view_w / 2.0, self.WORLD_WIDTH - view_w))
        top = max(0.0, min(center_y - view_h / 2.0, self.WORLD_HEIGHT - view_h))
        viewport = pygame.Rect(int(round(left)), int(round(top)), int(round(view_w)), int(round(view_h)))
        frame = self.world.subsurface(viewport)
        if zoom == 1.0:
            screen.blit(frame, (0, 0))
        else:
            screen.blit(pygame.transform.smoothscale(frame, screen.get_size()), (0, 0))

        # Animated fake short-form video on the phone. Convert its world position
        # into screen coordinates so it naturally leaves the viewport during the pan.
        phone_screen_y = (710 - top) * zoom
        if animate_phone and -295 < phone_screen_y < screen.get_height():
            video_rect = pygame.Rect(416, int(phone_screen_y), 168, 295)
            clip = screen.get_clip()
            screen.set_clip(video_rect)

            phase = elapsed * 2.2
            cx = 500 + int(34 * math.sin(phase))
            cy = int(phone_screen_y + 135 + 22 * math.cos(phase * 1.4))
            pygame.draw.rect(screen, (55, 76, 94), video_rect)
            pygame.draw.circle(screen, (225, 178, 122), (cx, cy), 32)
            pygame.draw.rect(screen, (120, 82, 135), (cx - 26, cy + 28, 52, 72), border_radius=12)
            pygame.draw.rect(screen, (235, 235, 235), (430, int(phone_screen_y + 260), 118, 5), border_radius=2)
            pygame.draw.circle(screen, (240, 240, 240), (563, int(phone_screen_y + 55)), 6)
            pygame.draw.circle(screen, (240, 240, 240), (563, int(phone_screen_y + 87)), 6)
            pygame.draw.circle(screen, (240, 240, 240), (563, int(phone_screen_y + 119)), 6)

            screen.set_clip(clip)
