import unittest
from unittest.mock import patch

from game.core.localization import detect_language, normalize_locale


class LocalizationTests(unittest.TestCase):
    def test_italian_locales(self):
        for value in ("it", "it_IT", "it_IT.UTF-8", "it-CH"):
            self.assertEqual("it", normalize_locale(value))

    def test_non_italian_locales_fall_back_to_english(self):
        for value in ("en_US.UTF-8", "de_CH", "fr_FR", None, ""):
            self.assertEqual("en", normalize_locale(value))

    @patch("game.core.localization._fallback_locale_candidates")
    @patch("game.core.localization._windows_user_locale", return_value="it-IT")
    def test_windows_italian_locale_takes_priority(self, _windows_locale, fallback):
        self.assertEqual("it", detect_language())
        fallback.assert_not_called()

    @patch("game.core.localization._fallback_locale_candidates")
    @patch("game.core.localization._windows_user_locale", return_value="de-DE")
    def test_non_italian_windows_locale_is_english(self, _windows_locale, fallback):
        self.assertEqual("en", detect_language())
        fallback.assert_not_called()

    @patch(
        "game.core.localization._fallback_locale_candidates",
        return_value=["it_CH.UTF-8"],
    )
    @patch("game.core.localization._windows_user_locale", return_value=None)
    def test_fallback_detection_still_supports_italian(self, _windows_locale, _fallback):
        self.assertEqual("it", detect_language())
