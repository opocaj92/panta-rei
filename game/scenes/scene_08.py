import pygame

from game.core.scene import Scene
from game.core.timing import CompletionTimer
from game.rendering.stella_pov_renderer import StellaPOVRenderer
from game.systems.approach import ApproachSystem


class Scene08(Scene):
    """Stella can optionally lean closer to Marco while speaking."""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.renderer = StellaPOVRenderer(config, game.assets)
        self.camera_y = 0.0
        self.elapsed = 0.0
        self.approach_system = ApproachSystem(config.get("approach", {}).get("drag_sensitivity", 0.0028))
        self.completion_timer = CompletionTimer()
        self.drag_sound_played = False

    def help_needed(self):
        return not self.transition_started and self.approach_system.progress < 1.0

    def enter(self):
        # Preserve the exact camera position passed by Scene 07.
        self.camera_y = float(self.incoming_state.get("camera_y", 0.0))
        self.approach_system.reset()
        self.drag_sound_played = False
        self.completion_timer.reset()
        self.game.dialogue.load("scene_08")
        # Scene 07 already crossfaded these channels during Stella's upward pan.
        # Do not restart the river, phone, wind, or vegetation here.

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.drag_sound_played = False
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.drag_sound_played = False
        before = self.approach_system.progress
        self.approach_system.handle_event(event, enabled=not self.transition_started)
        # Trigger only once per gesture, and only if Stella actually moves closer.
        if (event.type == pygame.MOUSEMOTION and not self.drag_sound_played
                and self.approach_system.progress > before):
            self.game.audio.play_sfx("scene08_grass_swish", volume=0.35)
            self.drag_sound_played = True

    def pinch_touch(self, distance_delta):
        """Android pinch input, independent of the desktop mouse-drag path."""
        before = self.approach_system.progress
        self.approach_system.pinch(distance_delta, enabled=not self.transition_started)
        if self.approach_system.progress > before and not self.drag_sound_played:
            self.game.audio.play_sfx("scene08_grass_swish", volume=0.35)
            self.drag_sound_played = True
        elif distance_delta < 0:
            # Allow a new swish on the next outward pinch.
            self.drag_sound_played = False

    def update(self, dt):
        self.game.audio.update_ambience_layers(dt)
        self.elapsed += dt
        self.approach_system.update(dt)
        self.game.dialogue.update(dt)

        elapsed = self.completion_timer.update(dt, active=self.game.dialogue.finished)
        if not self.game.dialogue.finished:
            return
        delay = float(self.config.get("post_dialogue_delay", 1.0))
        if elapsed >= delay and not self.transition_started:
            # Eye blink closes during the first half of transition_out.
            # Fade every environmental layer to silence by full black.
            transition = self.config.get("transition_out", {})
            duration = float(transition.get("duration", 0.0))
            fade_ms = round(duration * 500) if transition.get("type") == "eye_blink" else round(duration * 1000)
            for name in ("river", "wind", "vegetation", "phone"):
                self.game.audio.set_ambience_layer_volume(name, 0.0, fade_ms=fade_ms)
            self.request_transition(self.config.get("next_scene", "scene_09"), state={"camera_y": self.camera_y, "approach": self.approach_system.progress})

    def render(self, screen):
        approach_cfg = self.config.get("approach", {})
        max_zoom = float(approach_cfg.get("max_safe_zoom", 1.38))
        zoom = 1.0 + (max_zoom - 1.0) * self.approach_system.display_progress
        self.renderer.render(screen, self.camera_y, self.elapsed, zoom=zoom,
                             animate_phone=False, focus=(110, 285))

        self.render_dialogue_or_thought(
            screen, dialogue_rect=pygame.Rect(51, 273, screen.get_width() - 102, 66)
        )
