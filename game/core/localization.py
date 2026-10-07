import locale
import os
import sys


def normalize_locale(value):
    """Normalize a locale string to one of the game's supported languages."""
    if not value:
        return "en"
    normalized = str(value).strip().replace("-", "_").lower()
    return "it" if normalized == "it" or normalized.startswith("it_") else "en"


def _windows_user_locale():
    """Return the Windows user's locale name (for example ``it-IT``).

    Windows does not reliably expose its display/user locale through the
    POSIX-style environment variables used on Linux. Querying the native API
    first makes packaged Windows builds follow the user's Windows locale while
    keeping the implementation dependency-free.
    """
    if sys.platform != "win32":
        return None

    try:
        import ctypes

        locale_name_max_length = 85  # LOCALE_NAME_MAX_LENGTH from Windows API.
        buffer = ctypes.create_unicode_buffer(locale_name_max_length)
        result = ctypes.windll.kernel32.GetUserDefaultLocaleName(
            buffer, locale_name_max_length
        )
        return buffer.value if result else None
    except (AttributeError, OSError, TypeError, ValueError):
        # Fall through to Python/environment-based detection below. This also
        # keeps startup robust on unusual or restricted Windows environments.
        return None


def _fallback_locale_candidates():
    """Collect locale hints available through Python and the environment."""
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

    return candidates


def detect_language():
    """Return Italian for an Italian user locale; English for everything else.

    On Windows the native user locale is authoritative because POSIX locale
    variables are commonly absent. If that query is unavailable, or on other
    operating systems, Python/environment locale hints are used as fallbacks.
    """
    windows_locale = _windows_user_locale()
    if windows_locale:
        return normalize_locale(windows_locale)

    candidates = _fallback_locale_candidates()
    return "it" if any(normalize_locale(value) == "it" for value in candidates) else "en"
