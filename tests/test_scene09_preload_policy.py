"""Regression checks for the Scene 09 preloading policy."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Scene09PreloadPolicyTests(unittest.TestCase):
    def test_preload_is_guarded_during_dragging(self):
        tree = ast.parse((ROOT / "game/scenes/scene_09.py").read_text())
        scene = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Scene09")
        update = next(n for n in scene.body if isinstance(n, ast.FunctionDef) and n.name == "update")
        text = ast.unparse(update)
        self.assertIn("self.silhouette_drag.dragging", text)
        self.assertIn("self._preload_idle_elapsed", text)
        self.assertIn("self._advance_scene10_preload()", text)
        self.assertIn("self.transition_started", text)

    def test_idle_delay_configured(self):
        import json
        config = json.loads((ROOT / "data/scenes/scene_09.json").read_text())
        self.assertGreater(config["preload_idle_delay"], 0)


if __name__ == "__main__":
    unittest.main()
