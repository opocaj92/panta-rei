"""Tests that do not require a Pygame display or image assets."""
import pytest

from game.core.dialogue_manager import validate_dialogue
from game.core.timing import CompletionTimer
from game.core.config_validation import validate_scene_config


def test_completion_timer_resets_on_inactive_condition():
    timer = CompletionTimer()
    assert timer.update(.5, active=True) == .5
    assert timer.update(1, active=False) == 0
    assert timer.update(.25, active=True) == .25


def test_dialogue_rejects_invalid_speed_and_text():
    with pytest.raises(ValueError, match='speed'):
        validate_dialogue({'lines': [{'text': 'hello', 'speed': 0}]})
    with pytest.raises(ValueError, match='text'):
        validate_dialogue({'lines': [{'speaker': 'X'}]})


def test_post_complete_delay_is_validated():
    with pytest.raises(ValueError, match='post_complete_delay'):
        validate_scene_config('scene_10', {'id': 'scene_10', 'type': 'interactive', 'post_complete_delay': -1})
