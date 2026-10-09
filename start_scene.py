"""Launch Panta Rei directly into a selected scene.

Examples:
    python start_scene.py 2
    python start_scene.py 05
    python start_scene.py scene_08
"""
import argparse

from game.core.game import Game
from game.core.scene_manager import SCENES


def main():
    parser = argparse.ArgumentParser(description="Start Panta Rei at a chosen scene.")
    parser.add_argument("scene", help="Scene number (1-12) or scene_XX")
    args = parser.parse_args()

    raw = args.scene.strip().lower()
    if raw.startswith("scene_"):
        raw = raw[6:]
    if not raw.isdigit():
        parser.error("Scene must be a number from 1 to 12 (or scene_XX).")
    name = f"scene_{int(raw):02d}"
    if name not in SCENES:
        parser.error(f"Unknown scene {name}; choose 1 through 12.")

    # Restore the camera framing normally inherited from the preceding scene.
    state = {}
    if name == "scene_05":
        from game.core.world_data import load_world
        from game.core.config import WINDOW_WIDTH, WINDOW_HEIGHT
        world = load_world("river_estuary")
        x, y, w, h = world["estuary_region"]
        camera_x = max(0, min(x + w / 2 - WINDOW_WIDTH / 2,
                              world["width"] - WINDOW_WIDTH))
        camera_y = max(0, min(y + h / 2 - WINDOW_HEIGHT / 2,
                              world["height"] - WINDOW_HEIGHT))
        state = {"camera": [camera_x, camera_y], "flow_time": 0.0}
    elif name == "scene_08":
        from game.core.config import DATA_DIR
        import json
        with (DATA_DIR / "scenes" / "scene_07.json").open(encoding="utf-8") as file:
            previous = json.load(file)
        state = {"camera_y": float(previous.get("camera", {}).get("marco_y", 0.0))}

    Game().run(start_scene=name, start_state=state)


if __name__ == "__main__":
    main()
