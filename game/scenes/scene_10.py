import pygame

from game.core.scene import Scene
from game.core.timing import CompletionTimer
from game.rendering.river_sea_renderer import RiverSeaRenderer
from game.systems.river_drag import RiverDragSystem


class Scene10(Scene):
    """Pull the visible river leftward until it irreversibly joins the sea."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = None
        self.elapsed = 0.0
        self.river_drag = None
        self.completion_timer = CompletionTimer()
        self.arrival_played = False
        self.music_gain = 0.32

    @property
    def interaction_cfg(self):
        return self.config.get('interaction', {})

    def help_needed(self):
        return not self.river_drag.connected and not self.transition_started

    def enter(self):
        self.game.dialogue.load('scene_10')
        self.renderer = RiverSeaRenderer(self.game.assets)

        self.river_drag = RiverDragSystem(self.interaction_cfg, self.game.screen.get_size())
        self.arrival_played = False
        self.music_gain = 0.32
        # Scene 09 leaves this track playing: updating its volume does not restart it.
        self.game.audio.play_music("scene09_suspended_atmosphere", volume=self.music_gain)

    def handle_input(self, event):
        self.river_drag.handle_event(event)

    def update(self, dt):
        self.elapsed += dt
        start_x = self.river_drag.width * (1.0 - float(self.interaction_cfg.get('initial_visible_fraction', 0.05)))
        edge_x = self.river_drag.width * float(self.interaction_cfg.get('sea_edge_fraction', 0.31))
        progress = max(0.0, min(1.0, (start_x - self.river_drag.leading_x) / max(1.0, start_x - edge_x)))
        if self.river_drag.connected:
            progress = 1.0
        # Match Scene 09: only the shared suspended music grows with progress.
        target_music = 0.32 + 0.18 * progress
        smoothing = min(1.0, max(0.0, dt) * 2.5)
        self.music_gain += (target_music - self.music_gain) * smoothing
        if not self.transition_started:
            self.game.audio.play_music("scene09_suspended_atmosphere", volume=self.music_gain)
        if self.river_drag.connected and not self.arrival_played:
            self.arrival_played = True
            self.game.audio.play_sfx("scene09_meeting_harmony", volume=0.60)
            self.game.audio.play_sfx("scene09_kiss_shimmer", volume=0.32)
        self.game.dialogue.update(dt)
        if self.river_drag.connected and self.game.dialogue.finished:
            elapsed = self.completion_timer.update(dt, active=True)
            delay = float(self.config.get('post_complete_delay', 0.55))
            if elapsed >= delay and not self.transition_started:
                duration = float(self.config.get('transition_out', {}).get('duration', 0.0))
                self.game.audio.stop_music(fade_ms=round(duration * 1000))
                self.game.audio.fade_sfx('scene09_kiss_shimmer', fade_ms=round(duration * 1000))
                self.game.audio.fade_sfx('scene09_meeting_harmony', fade_ms=round(duration * 1000))
                self.request_transition(self.config.get('next_scene', 'scene_11'))
        else:
            self.completion_timer.reset()

    def exit(self):
        # Also release the loop if the scene is interrupted unexpectedly.
        if not self.transition_started:
            self.game.audio.fade_sfx('scene09_kiss_shimmer', fade_ms=120)
            self.game.audio.fade_sfx('scene09_meeting_harmony', fade_ms=120)

    def render(self, screen):
        self.renderer.render(screen, self.river_drag.leading_x, self.river_drag.connected, self.elapsed)
        self.game.text_renderer.dialogue(screen, self.game.dialogue)
