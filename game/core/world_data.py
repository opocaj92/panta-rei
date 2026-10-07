import json

from .config import DATA_DIR


def load_world(name):
    """Load immutable authored world geometry shared by multiple scenes."""
    path = DATA_DIR / "worlds" / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing world config: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("id") != name:
        raise ValueError(f"World config id mismatch: expected {name!r}, got {data.get('id')!r}")
    return data
