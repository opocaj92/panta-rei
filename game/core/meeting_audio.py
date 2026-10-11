"""Shared authored sound levels for the Scene 09/10 meeting effects."""
from functools import lru_cache
import json

from game.core.config import DATA_DIR
from game.core.config_validation import validate_scene_config


@lru_cache(maxsize=1)
def meeting_audio_volumes():
    """Read validated meeting volumes from their single authored source."""
    with (DATA_DIR / "scenes" / "scene_09.json").open(encoding="utf-8") as source:
        config = json.load(source)
    validate_scene_config("scene_09", config)
    audio = config["meeting_audio"]
    return float(audio["harmony_volume"]), float(audio["shimmer_volume"])
