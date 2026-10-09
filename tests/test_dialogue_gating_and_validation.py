"""Regression checks for scene-controlled dialogue and authored config errors."""
import pytest

from game.core.scene import Scene
from game.core.config_validation import validate_scene_config


def test_default_scene_allows_visible_dialogue():
    scene = Scene(None, {})
    assert scene.allows_dialogue_advance()


def test_scene02_blocks_dialogue_until_it_is_shown():
    pytest.importorskip('pygame')
    from game.scenes.scene_02 import Scene02
    scene = Scene02.__new__(Scene02)
    scene.progress_complete = False
    scene.dialogue_started = False
    scene.transition_started = False
    assert not scene.allows_dialogue_advance()
    scene.progress_complete = True
    assert not scene.allows_dialogue_advance()
    scene.dialogue_started = True
    assert scene.allows_dialogue_advance()


def test_scene07_blocks_dialogue_during_camera_pan():
    pytest.importorskip('pygame')
    from game.scenes.scene_07 import Scene07
    scene = Scene07.__new__(Scene07)
    scene.dialogue_started = False
    scene.transition_started = False
    assert not scene.allows_dialogue_advance()
    scene.dialogue_started = True
    assert scene.allows_dialogue_advance()


def test_scene05_help_stops_after_visible_stroke():
    pytest.importorskip('pygame')
    from game.scenes.scene_05 import Scene05
    scene = Scene05.__new__(Scene05)
    scene.has_traced_line = False
    scene.transition_started = False
    scene.game = type('GameStub', (), {'dialogue': type('DialogueStub', (), {'finished': False})()})()
    assert scene.help_needed()
    scene.has_traced_line = True
    assert not scene.help_needed()


def test_missing_scale_has_descriptive_error():
    config = {'id': 'scene_01', 'type': 'test', 'presentation': {
        'stella_placement': {'offset': [0, 0]}}}
    with pytest.raises(ValueError, match=r'scene_01.presentation.stella_placement.*scale'):
        validate_scene_config('scene_01', config)


def test_invalid_numeric_setting_has_descriptive_error():
    config = {'id': 'scene_01', 'type': 'test', 'help_delay': 'not-a-number'}
    with pytest.raises(ValueError, match=r'scene_01.help_delay'):
        validate_scene_config('scene_01', config)
