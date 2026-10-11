"""Regression checks for the shared soundscape and configurable scene tuning."""
import copy
import json
import unittest
from pathlib import Path

from game.core.config_validation import validate_audio_config, validate_scene_config
from game.core.riverbank_audio import riverbank_audio, riverbank_mix


class SharedAudioConfigurationTests(unittest.TestCase):
    def test_mix_override_does_not_mutate_shared_audio(self):
        original = riverbank_mix("stella")
        changed = riverbank_mix("stella", {"phone": 0.38})
        self.assertEqual(changed["phone"], 0.38)
        self.assertEqual(riverbank_mix("stella"), original)
        self.assertNotEqual(changed["phone"], original["phone"])

    def test_unknown_audio_layer_rejected(self):
        data = copy.deepcopy(riverbank_audio())
        data["mixes"]["river"]["unknown"] = 0.1
        with self.assertRaises(ValueError):
            validate_audio_config(data, context="test")

    def test_authored_scene_configs_validate(self):
        root = Path(__file__).resolve().parents[1]
        for number in (2, 7, 8, 9, 10):
            name = f"scene_{number:02d}"
            data = json.loads((root / "data" / "scenes" / f"{name}.json").read_text())
            with self.subTest(scene=name):
                validate_scene_config(name, data)

    def test_invalid_music_volume_rejected(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "data/scenes/scene_09.json").read_text())
        config["music"]["initial_volume"] = 0.95
        with self.assertRaises(ValueError):
            validate_scene_config("scene_09", config)
