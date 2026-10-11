"""Final regression checks for shared audio, activation and scene help."""
from types import SimpleNamespace
import pytest
from game.core.riverbank_audio import riverbank_mix
from game.core.meeting_audio import meeting_audio_volumes


def test_riverbank_overrides_are_validated_and_do_not_mutate_source():
    original = riverbank_mix("stella")
    modified = riverbank_mix("stella", {"phone": 0.38})
    assert modified["phone"] == 0.38
    assert riverbank_mix("stella") == original
    with pytest.raises(ValueError, match="Unknown riverbank audio layer"):
        riverbank_mix("stella", {"invalid": 0.3})
    with pytest.raises(ValueError, match="between 0 and 1"):
        riverbank_mix("stella", {"phone": 2})
    with pytest.raises(ValueError, match="finite"):
        riverbank_mix("stella", {"phone": float("nan")})


def test_meeting_audio_has_one_authored_source():
    assert meeting_audio_volumes() == (0.60, 0.32)


def test_activation_error_identifies_scene_and_stage(monkeypatch):
    class BrokenScene:
        def __init__(self, game, config):
            pass
        def reset_help(self):
            pass
        def enter(self):
            raise ValueError("test failure")

    pytest.importorskip("pygame")
    from game.core.scene_manager import SceneManager
    from game.core import scene_manager
    monkeypatch.setitem(scene_manager.SCENES, "test_scene", BrokenScene)
    manager = SceneManager(SimpleNamespace())
    monkeypatch.setattr(manager, "_load_config", lambda name: {})
    with pytest.raises(RuntimeError, match=r"test_scene.*enter\(\)"):
        manager._activate_scene("test_scene")
