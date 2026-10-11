"""Shared authored riverbank soundscape, used across Scenes 02, 07, 08, 11 and 12."""
import json
from functools import lru_cache
from game.core.config import DATA_DIR
from game.core.config_validation import _fraction


@lru_cache(maxsize=1)
def riverbank_audio():
    """Load the common soundscape once; callers must not mutate the result."""
    with (DATA_DIR / "audio" / "riverbank.json").open(encoding="utf-8") as source:
        config = json.load(source)
    from game.core.config_validation import validate_audio_config
    validate_audio_config(config, context="data/audio/riverbank.json")
    return config


def riverbank_mix(view, overrides=None):
    """Return an independent view mix with optional scene-specific overrides."""
    mix = dict(riverbank_audio()["mixes"][view])
    if overrides is not None:
        if not isinstance(overrides, dict):
            raise ValueError("riverbank audio overrides must be an object")
        for layer, gain in overrides.items():
            if layer not in mix:
                raise ValueError(f"Unknown riverbank audio layer: {layer!r}")
            _fraction(gain, f"riverbank override.{layer}")
        mix.update(overrides)
    return mix
