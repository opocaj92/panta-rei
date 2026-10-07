import locale
import os


def normalize_locale(value):
    """Normalize a locale string to the game's supported language code."""
    if not value:
        return "en"
    normalized = str(value).strip().replace("-", "_").lower()
    return "it" if normalized == "it" or normalized.startswith("it_") else "en"


def detect_language():
    """Return Italian only for an Italian system locale; English otherwise."""
    candidates = []
    try:
        current = locale.getlocale()[0]
        if current:
            candidates.append(current)
    except (ValueError, TypeError):
        pass

    for key in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        value = os.environ.get(key)
        if value:
            candidates.extend(value.split(":"))

    return "it" if any(normalize_locale(value) == "it" for value in candidates) else "en"
