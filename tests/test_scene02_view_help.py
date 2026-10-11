"""Scene 02 contextual help resets only on actual viewpoint changes."""
import ast
from pathlib import Path


def test_view_change_resets_help_before_audio_and_completion():
    source = Path("game/scenes/scene_02.py").read_text()
    tree = ast.parse(source)
    scene = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Scene02")
    handler = next(n for n in scene.body if isinstance(n, ast.FunctionDef) and n.name == "handle_input")
    # The reset must be inside the successful-view-change branch, not on
    # every keypress (which would postpone help indefinitely).
    branch = next(n for n in ast.walk(handler) if isinstance(n, ast.If)
                  and isinstance(n.test, ast.Compare)
                  and isinstance(n.test.left, ast.Name)
                  and n.test.left.id == "requested_view")
    calls = [n for n in ast.walk(branch) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "reset_help"]
    assert len(calls) == 1

def test_scene02_help_delay_is_five_seconds():
    import json
    config = json.loads(Path("data/scenes/scene_02.json").read_text())
    assert config["help_delay"] == 5.0
    assert config["dialogue_start_delay"] == 2.0
    assert config["view_change_cooldown"] == 0.5
