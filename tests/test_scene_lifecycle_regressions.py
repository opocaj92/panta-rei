"""Contracts for scene activation, help reset, and shared music smoothing."""
from types import SimpleNamespace

from game.core.scene import Scene
from game.core.timing import approach_linear


def test_activation_resets_help_and_requests_clock_reset(monkeypatch):
    import pytest
    pytest.importorskip("pygame")
    from game.core.scene_manager import SceneManager
    events = []

    class Destination(Scene):
        def __init__(self, game, config):
            super().__init__(game, config)
            self.help_visible = True  # Simulate reused/prepared state.
            self.help_wait_elapsed = 99.0

        def enter(self):
            events.append('enter')
            assert not self.help_visible
            assert self.help_wait_elapsed == 0.0

    class Previous(Scene):
        def exit(self):
            events.append('exit')

    class Transitions:
        def clear(self):
            events.append('clear')

    game = SimpleNamespace(
        audio=SimpleNamespace(enter_scene=lambda name: events.append('audio')),
        transitions=Transitions(),
        update_cursor_visibility=lambda: events.append('cursor'),
        _scene_clock_reset_requested=False,
    )
    manager = SceneManager(game)
    manager.current = Previous(game, {})
    monkeypatch.setitem(__import__('game.core.scene_manager', fromlist=['SCENES']).SCENES,
                        'scene_10', Destination)
    monkeypatch.setattr(manager, '_load_config', lambda name: {'transition_in': {'type': 'none'}})
    manager._activate_scene('scene_10')
    assert events.index('exit') < events.index('enter')
    assert manager.current_name == 'scene_10'
    assert game._scene_clock_reset_requested


def test_pending_transition_does_not_activate_early(monkeypatch):
    import pytest
    pytest.importorskip("pygame")
    from game.core.scene_manager import SceneManager
    callbacks = SimpleNamespace(transitions=SimpleNamespace(
        fade_to_black=lambda duration, on_complete: callbacks.append(on_complete)))
    manager = SceneManager(game)
    activated = []
    monkeypatch.setattr(manager, '_activate_scene', lambda name, **kw: activated.append((name, kw)))
    manager.change_scene('scene_10', {'type': 'fade_to_black', 'duration': 1.0})
    assert not activated
    assert manager.pending_scene == 'scene_10'
    callbacks.pop()()
    assert activated == [('scene_10', {'start_transition_in': True, 'state': None})]
    assert manager.pending_scene is None


def test_approach_linear_handles_negative_and_long_frames():
    assert approach_linear(.32, .5, -1, 2.5) == .32
    assert approach_linear(.32, .5, 1, 2.5) == .5
    assert abs(approach_linear(.32, .5, .1, 2.5) - .365) < 1e-10
