import unittest
from types import SimpleNamespace
from unittest.mock import patch


class _FakeInput:
    @staticmethod
    def held(_key):
        return False


class _FakeDialogue:
    finished = True

    @staticmethod
    def load(_name):
        pass

    @staticmethod
    def update(_dt):
        pass


class _FakeScenes:
    def __init__(self):
        self.calls = []

    def change_scene(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class Scene04TransitionTests(unittest.TestCase):
    def test_completion_requests_scene_change_only_once(self):
        try:
            import pygame
            from game.scenes.scene_04 import Scene04
        except ModuleNotFoundError as exc:
            self.skipTest(f"pygame unavailable: {exc}")

        game = SimpleNamespace(
            input=_FakeInput(),
            dialogue=_FakeDialogue(),
            scenes=_FakeScenes(),
            screen=SimpleNamespace(get_size=lambda: (1000, 600)),
        )
        config = {
            "world": "river_estuary",
            "camera_start": [0, 1500],
            "camera_speed": 360.0,
            "estuary": {"required_visible_fraction": 0.6},
            "next_scene": "scene_05",
            "transition_out": {"type": "none", "duration": 0.0},
        }

        with patch("game.scenes.scene_04.RiverWorldRenderer"):
            scene = Scene04(game, config)

        scene._check_estuary_visibility = lambda: setattr(scene, "estuary_visible", True)
        scene.update(1 / 60)
        scene.update(1 / 60)

        self.assertTrue(scene.transition_started)
        self.assertEqual(1, len(game.scenes.calls))
