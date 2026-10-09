"""Regression checks for shared POV scene interfaces and configuration."""
import json
from pathlib import Path
from types import SimpleNamespace

from game.core.config_validation import validate_scene_config
import pytest
pytest.importorskip("pygame")
from game.scenes.scene_08 import Scene08
from game.rendering.stella_pov_renderer import StellaPOVRenderer

ROOT = Path(__file__).resolve().parents[1]

def test_scene08_localized_help_and_configuration():
    cfg = json.loads((ROOT / "data/scenes/scene_08.json").read_text())
    validate_scene_config("scene_08", cfg)
    assert cfg["help"]["en"] and cfg["help"]["it"]

def test_scene12_phone_rect_api():
    assert callable(StellaPOVRenderer.phone_screen_rect)

def test_scene08_consumes_camera_state_without_loading_assets():
    scene = Scene08.__new__(Scene08)
    scene.incoming_state = {"camera_y": 12.5}
    scene.game = SimpleNamespace(dialogue=SimpleNamespace(load=lambda name: None))
    Scene08.enter(scene)
    assert scene.camera_y == 12.5

def test_scene08_help_ends_at_maximum_approach():
    scene = Scene08.__new__(Scene08)
    scene.transition_started = False
    scene.approach = 0.5
    assert scene.help_needed()
    scene.approach = 1.0
    assert not scene.help_needed()
