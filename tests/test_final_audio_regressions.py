"""Focused contracts for the late-game audio handoffs and credits."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def source(relative):
    return (ROOT / relative).read_text(encoding='utf-8')


def test_scene09_to_10_preserves_atmosphere():
    nine = source('game/scenes/scene_09.py')
    ten = source('game/scenes/scene_10.py')
    assert 'scene09_suspended_atmosphere' in nine
    assert 'scene09_suspended_atmosphere' in ten
    assert 'restart=True' not in ten


def test_scene10_merger_effects_are_one_shot_and_fade_on_exit():
    tree = ast.parse(source('game/scenes/scene_10.py'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Scene10')
    update = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'update')
    guards = [n for n in ast.walk(update) if isinstance(n, ast.If)]
    assert any('not self.arrival_played' in ast.unparse(n.test) for n in guards)
    text = source('game/scenes/scene_10.py')
    for effect in ('scene09_kiss_shimmer', 'scene10_arrival_resolution'):
        assert f"fade_sfx('{effect}'" in text


def test_scene11_crossfade_tracks_camera():
    text = source('game/scenes/scene_11.py')
    assert 'set_ambience_layer_volume' in text
    assert 'sky' in text.lower()


def test_scene12_ends_in_silence():
    text = source('game/scenes/scene_12.py')
    assert 'stop_music()' in text
    assert 'stop_ambience_layers()' in text
    assert 'stop_ambience()' in text
    assert 'scene12_final_credits' in text


def test_credits_static_surface_is_cached():
    text = source('game/rendering/phone_credits_renderer.py')
    assert 'self._static_cache' in text
    assert 'self._static_cache[key] = static' in text
