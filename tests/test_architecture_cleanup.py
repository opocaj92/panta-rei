"""Small contracts for the shared configuration and rendering architecture."""
from game.core.presentation import deep_merge


def test_deep_merge_preserves_nested_siblings_and_inputs():
    base = {"marco": {"height": 245, "left": 62}, "phone": [1, 2]}
    override = {"marco": {"height": 260}}
    result = deep_merge(base, override)
    assert result == {"marco": {"height": 260, "left": 62}, "phone": [1, 2]}
    result["marco"]["left"] = 999
    assert base["marco"]["left"] == 62
    assert override == {"marco": {"height": 260}}


def test_animation_is_owned_by_systems():
    from game.systems.animation import LoopingAnimation
    assert LoopingAnimation.__module__ == "game.systems.animation"


def test_shared_presentation_errors_are_actionable(tmp_path, monkeypatch):
    import pytest
    import game.core.presentation as presentation
    monkeypatch.setattr(presentation, "DATA_DIR", tmp_path)
    with pytest.raises(FileNotFoundError, match="Shared presentation"):
        presentation.shared_presentation("missing")
