"""Regression contracts for the third refactoring pass."""
from types import SimpleNamespace

import pytest

from game.core.dialogue_manager import validate_dialogue
from game.core.scene import Scene
from game.core.timing import CompletionTimer


def test_missing_lines_are_not_silent_empty_dialogue():
    with pytest.raises(ValueError, match='lines'):
        validate_dialogue({})
    assert validate_dialogue({'lines': []}) == []


def test_transition_request_restores_guard_on_error():
    class BrokenManager:
        def change_scene(self, *args, **kwargs):
            raise RuntimeError('transition failed')

    scene = Scene(SimpleNamespace(scenes=BrokenManager()), {})
    with pytest.raises(RuntimeError, match='transition failed'):
        scene.request_transition('scene_02')
    assert scene.transition_started is False


def test_completion_timer_ignores_negative_delta():
    timer = CompletionTimer()
    timer.update(.4, active=True)
    assert timer.update(-2, active=True) == .4
