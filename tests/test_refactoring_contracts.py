"""Regression tests for shared scene and caching contracts."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
pytest.importorskip("pygame")

from game.core.asset_manager import AssetManager
from game.core.scene_manager import SceneManager
from game.systems.animation import LoopingAnimation
from game.scenes.scene_03 import Scene03
from game.scenes.scene_06 import Scene06


def test_animation_advances_multiple_loops():
    animation = LoopingAnimation([0, 1, 2], fps=10)
    animation.update(1.2)
    assert animation.frame_index == 0
    animation.update(0.1)
    assert animation.frame_index == 1


def test_asset_cache_rejects_conflicting_image_spec():
    assets = AssetManager()
    assets._image_specs['x'] = ('image.png', True)
    with pytest.raises(ValueError, match='conflicting'):
        assets.image('x', 'other.png')


def test_asset_cache_rejects_conflicting_font_spec():
    assets = AssetManager()
    assets._font_specs[('x', 20)] = 'font.ttf'
    with pytest.raises(ValueError, match='different path'):
        assets.font('x', 'other.ttf', 20)


def test_invalid_destination_does_not_exit_current_scene(monkeypatch):
    manager = SceneManager(SimpleNamespace(transitions=Mock()))
    current = Mock()
    manager.current = current
    manager.current_name = 'scene_01'
    monkeypatch.setattr(manager, '_load_config', Mock(side_effect=ValueError('bad config')))
    with pytest.raises(ValueError, match='bad config'):
        manager._activate_scene('scene_02')
    current.exit.assert_not_called()
    assert manager.current is current
    assert manager.current_name == 'scene_01'


def make_game():
    dialogue = SimpleNamespace(finished=False, load=Mock(), update=Mock())
    scenes = SimpleNamespace(change_scene=Mock())
    return SimpleNamespace(dialogue=dialogue, scenes=scenes)


def test_scene03_delay_counts_from_entry():
    game = make_game()
    scene = Scene03(game, {'auto_delay': 1.5})
    scene.enter()
    scene.update(1.0)
    game.dialogue.finished = True
    scene.update(0.5)
    scene.update(0.5)
    game.scenes.change_scene.assert_called_once_with('scene_04', transition_config=None)


def test_scene06_delay_counts_from_dialogue_completion():
    game = make_game()
    scene = Scene06(game, {'post_dialogue_delay': 1.0})
    scene.enter()
    scene.update(10.0)
    game.dialogue.finished = True
    scene.update(0.5)
    game.scenes.change_scene.assert_not_called()
    scene.update(0.5)
    scene.update(0.5)
    game.scenes.change_scene.assert_called_once_with('scene_07', transition_config=None)
