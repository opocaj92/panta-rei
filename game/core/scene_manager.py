import json

from game.core.config import DATA_DIR
from game.core.config_validation import validate_scene_config
from game.scenes.scene_01 import Scene01
from game.scenes.scene_02 import Scene02
from game.scenes.scene_03 import Scene03
from game.scenes.scene_04 import Scene04
from game.scenes.scene_05 import Scene05
from game.scenes.scene_06 import Scene06
from game.scenes.scene_07 import Scene07
from game.scenes.scene_08 import Scene08
from game.scenes.scene_09 import Scene09
from game.scenes.scene_10 import Scene10
from game.scenes.scene_11 import Scene11
from game.scenes.scene_12 import Scene12


SCENES = {
    "scene_01": Scene01,
    "scene_02": Scene02,
    "scene_03": Scene03,
    "scene_04": Scene04,
    "scene_05": Scene05,
    "scene_06": Scene06,
    "scene_07": Scene07,
    "scene_08": Scene08,
    "scene_09": Scene09,
    "scene_10": Scene10,
    "scene_11": Scene11,
    "scene_12": Scene12,
}


class SceneManager:
    """Creates scenes and injects their JSON configuration."""

    def __init__(self, game):
        self.game = game
        self.current = None
        self.current_name = None
        self.pending_scene = None
        self.pending_state = None

    def _load_config(self, name):
        path = DATA_DIR / "scenes" / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing scene config: {path}")

        with path.open("r", encoding="utf-8") as f:
            config = json.load(f)

        validate_scene_config(name, config)
        return config

    def change_scene(self, name, transition_config=None, state=None):
        if name not in SCENES:
            raise ValueError(f"Unknown scene: {name}")
        if self.pending_scene is not None:
            raise RuntimeError(
                f"Cannot transition to {name!r}; transition to {self.pending_scene!r} is already pending"
            )

        if transition_config:
            transition_type = transition_config.get("type", "none")
            duration = float(transition_config.get("duration", 0.0))

            if transition_type == "fade_to_black" and duration > 0:
                self.pending_scene = name
                self.pending_state = state
                self.game.transitions.fade_to_black(
                    duration,
                    on_complete=self.finish_pending_transition,
                )
                return

            if transition_type == "eye_blink" and duration > 0:
                self.pending_scene = name
                self.pending_state = state
                self.game.transitions.eye_blink(
                    duration,
                    on_closed=self.finish_pending_blink,
                )
                return

        self._activate_scene(name, state=state)

    def _activate_scene(self, name, start_transition_in=True, state=None):
        if self.current:
            self.current.exit()

        config = self._load_config(name)
        self.current_name = name
        self.current = SCENES[name](self.game, config)
        self.current.incoming_state = state or {}
        self.current.enter()
        if start_transition_in:
            self._start_transition_in(config.get("transition_in"))

    def _start_transition_in(self, transition_config):
        if not transition_config:
            self.game.transitions.clear()
            return

        transition_type = transition_config.get("type", "none")
        duration = float(transition_config.get("duration", 0.0))

        if transition_type == "fade_from_black" and duration > 0:
            self.game.transitions.fade_from_black(duration)
        elif transition_type == "none":
            self.game.transitions.clear()

    def finish_pending_transition(self):
        if self.pending_scene is None:
            return

        scene_name = self.pending_scene
        state = self.pending_state
        self.pending_scene = None
        self.pending_state = None
        self._activate_scene(scene_name, state=state)


    def finish_pending_blink(self):
        if self.pending_scene is None:
            return

        scene_name = self.pending_scene
        state = self.pending_state
        self.pending_scene = None
        self.pending_state = None
        # Keep the blink transition alive while swapping scenes at full black.
        self._activate_scene(scene_name, start_transition_in=False, state=state)

    def handle_input(self, event):
        if self.current:
            self.current.handle_input(event)

    def update(self, dt):
        if self.current:
            self.current.update_help(dt)
            self.current.update(dt)

    def render(self, screen):
        if self.current:
            self.current.render(screen)
            self.current.render_help(screen)
