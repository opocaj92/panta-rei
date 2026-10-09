"""Resolve shared visual presets with independent nested scene overrides."""
import copy
import json
from game.core.config import DATA_DIR


def deep_merge(base, overrides):
    """Return a new dictionary; nested mappings merge, other values replace."""
    result = copy.deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def shared_presentation(name):
    """Return a fresh copy of a named presentation preset."""
    path = DATA_DIR / "presentation" / (name + ".json")
    if not path.is_file():
        raise FileNotFoundError(f"Shared presentation {name!r} not found: {path}")
    try:
        with path.open(encoding="utf-8") as source:
            preset = json.load(source)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in shared presentation {name!r}: {path}") from exc
    if not isinstance(preset, dict):
        raise ValueError(f"Shared presentation {name!r} must contain a JSON object: {path}")
    return preset


def with_shared_presentation(config, name):
    """Allow scenes to override individual nested values of shared presets."""
    merged = copy.deepcopy(config)
    merged["presentation"] = deep_merge(shared_presentation(name), config.get("presentation", {}))
    return merged
