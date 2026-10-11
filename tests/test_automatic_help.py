from types import SimpleNamespace

from game.core.scene import Scene


class DummyTextRenderer:
    def __init__(self):
        self.calls = []

    def help(self, screen, text):
        self.calls.append(text)


class InteractiveScene(Scene):
    def __init__(self, game, config):
        super().__init__(game, config)
        self.waiting = True

    def help_needed(self):
        return self.waiting


def make_scene(**config):
    game = SimpleNamespace(language="en", text_renderer=DummyTextRenderer())
    base = {"help": {"en": "Try the interaction.", "it": "Prova l'interazione."}}
    base.update(config)
    return InteractiveScene(game, base)


def test_help_appears_after_default_five_seconds():
    scene = make_scene()
    scene.update_help(4.0)
    assert not scene.help_visible
    scene.update_help(1.0)
    assert scene.help_visible


def test_progress_does_not_restart_countdown_or_dismiss_visible_help():
    scene = make_scene()
    scene.update_help(5.0)
    scene.update_help(3.0)
    assert scene.help_visible
    scene.update_help(100.0)
    assert scene.help_visible
    scene.render_help(None)
    assert scene.game.text_renderer.calls == ["Try the interaction."]


def test_help_disappears_only_when_no_longer_needed():
    scene = make_scene()
    scene.update_help(8.0)
    scene.waiting = False
    scene.update_help(0.1)
    assert not scene.help_visible
    assert scene.help_wait_elapsed == 0.0


def test_negative_delta_does_not_advance_help():
    scene = make_scene()
    scene.update_help(-5.0)
    assert scene.help_wait_elapsed == 0.0


def test_scene_specific_help_delay_and_reset():
    scene = make_scene(help_delay=8.0)
    scene.update_help(7.0)
    assert not scene.help_visible
    scene.update_help(1.0)
    assert scene.help_visible
    scene.reset_help()
    assert not scene.help_visible
    assert scene.help_wait_elapsed == 0.0
