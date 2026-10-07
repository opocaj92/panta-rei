from types import SimpleNamespace

from game.core.scene import Scene


class DummyTextRenderer:
    def help(self, screen, text):
        pass


class InteractiveScene(Scene):
    def __init__(self, game, config):
        super().__init__(game, config)
        self.waiting = True

    def help_needed(self):
        return self.waiting


def make_scene(**config):
    game = SimpleNamespace(language="en", text_renderer=DummyTextRenderer())
    base = {
        "help": {"en": "Try the interaction.", "it": "Prova l'interazione."},
        "help_delay": 2.0,
        "help_duration": 1.0,
    }
    base.update(config)
    return InteractiveScene(game, base)


def test_help_appears_after_inactivity():
    scene = make_scene()
    scene.update_help(1.0)
    assert scene.help_timer == 0.0
    scene.update_help(1.0)
    assert scene.help_timer == 1.0


def test_meaningful_progress_restarts_inactivity_clock():
    scene = make_scene()
    scene.update_help(1.5)
    scene.mark_help_progress()
    scene.update_help(1.0)
    assert scene.help_timer == 0.0
    scene.update_help(1.0)
    assert scene.help_timer == 1.0


def test_help_is_suppressed_when_player_action_is_not_required():
    scene = make_scene()
    scene.waiting = False
    scene.update_help(10.0)
    assert scene.help_timer == 0.0
    assert scene.help_inactivity == 0.0
