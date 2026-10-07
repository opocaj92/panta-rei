import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


class ProjectDataTests(unittest.TestCase):
    def test_scene_ids_and_next_scenes(self):
        configs = {}
        for path in sorted((DATA / "scenes").glob("scene_*.json")):
            cfg = json.loads(path.read_text(encoding="utf-8")); configs[path.stem] = cfg
            self.assertEqual(path.stem, cfg["id"])
        for name, cfg in configs.items():
            if "next_scene" in cfg:
                self.assertIn(cfg["next_scene"], configs, name)

    def test_localized_dialogue_has_matching_structure(self):
        it = {p.name: p for p in (DATA / "dialogue" / "it").glob("*.json")}
        en = {p.name: p for p in (DATA / "dialogue" / "en").glob("*.json")}
        self.assertEqual(set(it), set(en))
        for name in it:
            a=json.loads(it[name].read_text(encoding="utf-8"))["lines"]
            b=json.loads(en[name].read_text(encoding="utf-8"))["lines"]
            self.assertEqual(len(a),len(b),name)
            self.assertEqual([x.get("type","dialogue") for x in a],[x.get("type","dialogue") for x in b],name)
            for line in a+b:
                self.assertGreater(float(line.get("speed",40)),0)
                self.assertGreaterEqual(float(line.get("delay",0.8)),0)

    def test_interactive_help_is_bilingual(self):
        for n in (2,4,5,7,8,9,10,11):
            cfg=json.loads((DATA/'scenes'/f'scene_{n:02}.json').read_text(encoding='utf-8'))
            self.assertEqual({'it','en'},set(cfg['help']))

    def test_scene08_help_matches_one_way_mechanic(self):
        cfg=json.loads((DATA/'scenes'/'scene_08.json').read_text(encoding='utf-8'))
        self.assertNotIn('away',cfg['help']['en'].lower())
        self.assertNotIn('lontano',cfg['help']['it'].lower())

    def test_shared_river_world_is_single_source(self):
        world=json.loads((DATA/'worlds'/'river_estuary.json').read_text(encoding='utf-8'))
        self.assertEqual('river_estuary',world['id']); self.assertGreater(len(world['river_points']),2)
        for scene in ('scene_04','scene_05'):
            cfg=json.loads((DATA/'scenes'/f'{scene}.json').read_text(encoding='utf-8'))
            self.assertEqual('river_estuary',cfg['world'])
            self.assertNotIn('river_points',cfg)

    def test_all_scene_configs_pass_runtime_validation(self):
        from game.core.config_validation import validate_scene_config

        for path in sorted((DATA / "scenes").glob("scene_*.json")):
            config = json.loads(path.read_text(encoding="utf-8"))
            validate_scene_config(path.stem, config)
