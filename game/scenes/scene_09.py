import pygame

from game.core.scene import Scene
from game.core.timing import approach_linear
from game.rendering.silhouette_renderer import SilhouetteRenderer
from game.rendering.river_sea_renderer import RiverSeaRenderer
from game.systems.silhouette_drag import SilhouetteDragSystem


class Scene09(Scene):
    """Two silhouettes approach, meet briefly, then move apart."""

    APPROACHING = "approaching"
    JOINED = "joined"
    SEPARATING = "separating"
    COMPLETE = "complete"

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = SilhouetteRenderer(self.game.assets)
        self.elapsed = 0.0
        self.phase = self.APPROACHING
        self.separation = 0.0
        self.joined_elapsed = 0.0
        self.silhouette_drag = SilhouetteDragSystem()
        self.interaction_finished = False
        self.meeting_flash_elapsed = None
        self.meeting_flash_outline = None
        self.meeting_flash_size = None
        # Cache authored values once; scene configuration is immutable at runtime.
        interaction = self.interaction_cfg
        music = self.config.get("music", {})
        meeting = self.config.get("meeting_audio", {})
        flash = self.config.get("meeting_flash", {})
        self.start_separation = float(interaction.get("start_separation", 118.0))
        self.final_separation = float(interaction.get("final_separation", 118.0))
        self.join_threshold = float(interaction.get("join_threshold", 3.0))
        self.drag_sensitivity = float(interaction.get("drag_sensitivity", 1.0))
        self.joined_lock_duration = float(interaction.get("joined_lock_duration", 2.0))
        self.music_initial_volume = float(music.get("initial_volume", 0.32))
        self.music_increase = float(music.get("progress_volume_increase", 0.18))
        self.music_smoothing = float(music.get("smoothing_rate", 2.4))
        self.music_fade_in_ms = int(music.get("fade_in_ms", 900))
        self.harmony_volume = float(meeting.get("harmony_volume", 0.60))
        self.shimmer_volume = float(meeting.get("shimmer_volume", 0.32))
        self.flash_fade_in = float(flash.get("fade_in_duration", 0.15))
        self.flash_fade_out = float(flash.get("fade_out_duration", 0.40))
        self.music_gain = self.music_initial_volume
        self._scene10_preloader = None

    def help_needed(self):
        return self.phase in (self.APPROACHING, self.SEPARATING)

    @property
    def interaction_cfg(self):
        return self.config.get("interaction", {})

    def enter(self):
        self.game.dialogue.load("scene_09")
        self.separation = self.start_separation
        self.meeting_flash_elapsed = None
        self.meeting_flash_outline = None
        self.meeting_flash_size = None
        self.silhouette_drag.stop()
        self.music_gain = self.music_initial_volume
        # Scene 08 fades the riverside ambience during its exit transition.
        # Scene 09 is an abstract interlude with its own continuous music.
        self.game.audio.play_music(
            "scene09_suspended_atmosphere", fade_ms=self.music_fade_in_ms,
            volume=self.music_gain,
        )

        # Distribute Scene 10 image loading and scaling over Scene 09 frames.
        self.game.preloaded_scene10_renderer = None
        # Ownership: Scene 09 prepares the renderer, Game holds the completed
        # result temporarily, and Scene 10 consumes and clears that reference.
        self._scene10_preloader = RiverSeaRenderer.preload_steps(
            self.game.assets, self.game.screen.get_size()
        )

    def handle_input(self, event):
        if self.phase == self.JOINED or self.phase == self.COMPLETE:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            side = self._silhouette_side_at(event.pos)
            if side is not None:
                self.silhouette_drag.start(side, event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.silhouette_drag.stop()
        elif event.type == pygame.MOUSEMOTION and self.silhouette_drag.dragging:
            radial_delta = self.silhouette_drag.delta(
                event, self.drag_sensitivity,
                approaching=self.phase == self.APPROACHING,
            )
            # Directional clamp: during approach only inward motion counts;
            # after the meeting only outward motion counts. Neither can cross.
            if self.phase == self.APPROACHING:
                radial_delta = min(0.0, radial_delta)
            elif self.phase == self.SEPARATING:
                radial_delta = max(0.0, radial_delta)
            self.separation += radial_delta

            if self.phase == self.APPROACHING:
                self.separation = max(0.0, min(self.separation, self.start_separation))

                if self.separation <= self.join_threshold:
                    self.separation = 0.0
                    self.phase = self.JOINED
                    self.joined_elapsed = 0.0
                    self.game.audio.play_sfx("scene09_meeting_harmony", volume=self.harmony_volume)
                    # Flash is triggered halfway through the joined pause.
                    self.meeting_flash_elapsed = None
                    self.meeting_flash_outline = None
                    self.silhouette_drag.stop()
            elif self.phase == self.SEPARATING:
                target = self.final_separation
                self.separation = max(0.0, min(self.separation, target))

                if self.separation >= target:
                    self.separation = target
                    self.phase = self.COMPLETE
                    self.interaction_finished = True
                    self.silhouette_drag.stop()

    def _silhouette_side_at(self, pos):
        return self.renderer.side_at(self.game.screen, pos, self.separation)

    def update(self, dt):
        if self._scene10_preloader is not None:
            try:
                next(self._scene10_preloader)
            except StopIteration as completed:
                self.game.preloaded_scene10_renderer = completed.value
                self._scene10_preloader = None
        self.elapsed += dt
        # As the two figures approach, gently raise the atmospheric texture.
        start = max(1.0, self.start_separation)
        proximity = 1.0 - max(0.0, min(1.0, self.separation / start))
        target_gain = self.music_initial_volume
        if self.phase in (self.APPROACHING, self.JOINED):
            target_gain += self.music_increase * proximity
        self.music_gain = approach_linear(
            self.music_gain, target_gain, dt, self.music_smoothing,
        )
        if not self.transition_started:
            self.game.audio.play_music("scene09_suspended_atmosphere", volume=self.music_gain)
        if self.meeting_flash_elapsed is not None:
            self.meeting_flash_elapsed += dt
            if self.meeting_flash_elapsed >= self.flash_duration:
                self.meeting_flash_elapsed = None
                self.meeting_flash_outline = None
        self.game.dialogue.update(dt)

        if self.phase == self.JOINED:
            # JOINED deliberately ignores input: the temporary lock embodies the
            # dialogue's instant of union before separation becomes possible.
            previous_joined_elapsed = self.joined_elapsed
            self.joined_elapsed += dt
            joined_duration = self.joined_lock_duration
            midpoint = joined_duration / 2.0
            if previous_joined_elapsed < midpoint <= self.joined_elapsed:
                # Start precisely when the joined pause crosses its midpoint.
                self.meeting_flash_elapsed = self.joined_elapsed - midpoint
                # Trigger on the same update tick as the first visible flash frame.
                self.game.audio.play_sfx("scene09_kiss_shimmer", volume=self.shimmer_volume)
                self.meeting_flash_outline = None
            if self.joined_elapsed >= joined_duration:
                self.phase = self.SEPARATING


        if self.game.dialogue.finished and self.interaction_finished and not self.transition_started:
            # Preserve the same musical playback position into Scene 10.
            self.request_transition(self.config.get("next_scene", "scene_10"))

    @property
    def flash_duration(self):
        return self.flash_fade_in + self.flash_fade_out

    def _draw_meeting_flash(self, screen):
        """A brief pixel-sharp halo around the *combined* joined silhouettes."""
        if self.meeting_flash_elapsed is None:
            return
        size = screen.get_size()
        if self.meeting_flash_outline is None or self.meeting_flash_size != size:
            # Compose the two opaque shapes into one mask, so the glow follows
            # their shared exterior instead of drawing two overlapping halos.
            boy_rect, girl_rect = self.renderer.rects(screen, 0.0)
            left = max(0, min(boy_rect.left, girl_rect.left) - 6)
            top = max(0, min(boy_rect.top, girl_rect.top) - 6)
            right = min(size[0], max(boy_rect.right, girl_rect.right) + 6)
            bottom = min(size[1], max(boy_rect.bottom, girl_rect.bottom) + 6)
            if right <= left or bottom <= top:
                return
            shape = pygame.Surface((right - left, bottom - top), pygame.SRCALPHA)
            shape.blit(self.renderer.boy, (boy_rect.left - left, boy_rect.top - top))
            shape.blit(self.renderer.girl, (girl_rect.left - left, girl_rect.top - top))
            mask = pygame.mask.from_surface(shape, 30)
            points = mask.outline()
            if len(points) < 2:
                return
            outline = pygame.Surface(shape.get_size(), pygame.SRCALPHA)
            # Both passes use hard pixel edges; the low-alpha wider line is
            # the halo, while the narrower stroke gives the meeting its sparkle.
            pygame.draw.lines(outline, (235, 240, 255, 65), True, points, 5)
            pygame.draw.lines(outline, (255, 250, 238, 220), True, points, 2)
            self.meeting_flash_outline = (outline, (left, top))
            self.meeting_flash_size = size

        t = self.meeting_flash_elapsed
        # Derive total lifetime from the two authored fade durations.
        fade_in = self.flash_fade_in
        fade_out = self.flash_fade_out
        strength = min(1.0, t / fade_in) if t < fade_in else max(0.0, (self.flash_duration - t) / fade_out)
        outline, pos = self.meeting_flash_outline
        outline.set_alpha(round(255 * strength))
        screen.blit(outline, pos)

    def render(self, screen):
        self.renderer.render(screen, self.separation, self.phase, self.elapsed)
        self._draw_meeting_flash(screen)
        line = self.game.dialogue.current_line
        if line and line.get("type") == "thought":
            self.game.text_renderer.thought(screen, self.game.dialogue)
        else:
            self.game.text_renderer.dialogue(screen, self.game.dialogue)
