import json

from game.core import dialogue_manager as dialogue_module
from game.core.dialogue_manager import DialogueManager


def _write_dialogue(tmp_path):
    dialogue_dir = tmp_path / "dialogue" / "en"
    dialogue_dir.mkdir(parents=True)
    (dialogue_dir / "scene_test.json").write_text(
        json.dumps(
            {
                "lines": [
                    {"text": "First line", "speed": 10},
                    {"text": "Second line", "speed": 10},
                ]
            }
        ),
        encoding="utf-8",
    )


def test_dialogue_waits_for_player_after_line_finishes(tmp_path, monkeypatch):
    _write_dialogue(tmp_path)
    monkeypatch.setattr(dialogue_module, "DATA_DIR", tmp_path)
    dialogue = DialogueManager("en")
    dialogue.load("scene_test")

    dialogue.update(100.0)
    assert dialogue.current_text_complete
    assert dialogue.index == 0

    dialogue.update(100.0)
    assert dialogue.index == 0
    assert not dialogue.finished


def test_advance_first_completes_then_advances(tmp_path, monkeypatch):
    _write_dialogue(tmp_path)
    monkeypatch.setattr(dialogue_module, "DATA_DIR", tmp_path)
    dialogue = DialogueManager("en")
    dialogue.load("scene_test")

    dialogue.update(0.1)
    assert not dialogue.current_text_complete

    dialogue.advance()
    assert dialogue.current_text_complete
    assert dialogue.index == 0

    dialogue.advance()
    assert dialogue.index == 1
    assert dialogue.visible_characters == 0.0

    dialogue.advance()
    assert dialogue.current_text_complete
    assert dialogue.index == 1

    dialogue.advance()
    assert dialogue.finished
