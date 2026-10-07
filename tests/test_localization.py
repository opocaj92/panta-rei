import unittest
from game.core.localization import normalize_locale

class LocalizationTests(unittest.TestCase):
    def test_italian_locales(self):
        for value in ('it','it_IT','it_IT.UTF-8','it-CH'):
            self.assertEqual('it', normalize_locale(value))
    def test_non_italian_locales_fall_back_to_english(self):
        for value in ('en_US.UTF-8','de_CH','fr_FR',None,''):
            self.assertEqual('en', normalize_locale(value))
