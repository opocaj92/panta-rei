"""Touch input regression checks (skipped if pygame is unavailable)."""
import os
import unittest
from types import SimpleNamespace

try:
    import pygame
    from game.systems.touch_gestures import TouchGestures
except ImportError:
    pygame = None


@unittest.skipIf(pygame is None, 'pygame not installed')
class TouchGesturesTests(unittest.TestCase):
    def setUp(self):
        self.game = SimpleNamespace(
            display=SimpleNamespace(get_size=lambda: (640, 360)),
            logical_mouse=lambda p: (round(p[0]), round(p[1])),
            scenes=SimpleNamespace(current_name='scene_04'))
        self.touch = TouchGestures(self.game)

    def finger(self, kind, x, y, finger_id=1):
        return pygame.event.Event(kind, x=x / 640, y=y / 360, finger_id=finger_id)

    def test_scene04_drag_pans_without_dialogue(self):
        self.touch.handle(self.finger(pygame.FINGERDOWN, 100, 100))
        events, tap, delta = self.touch.handle(self.finger(pygame.FINGERMOTION, 145, 125))
        self.assertEqual(events, [])
        self.assertFalse(tap)
        self.assertEqual(delta, (45, 25))
        _, tap, _ = self.touch.handle(self.finger(pygame.FINGERUP, 145, 125))
        self.assertFalse(tap)

    def test_tap_and_swipe_are_distinct(self):
        self.game.scenes.current_name = 'scene_11'
        self.touch.handle(self.finger(pygame.FINGERDOWN, 200, 200))
        events, tap, _ = self.touch.handle(self.finger(pygame.FINGERUP, 201, 199))
        self.assertTrue(tap)
        self.assertFalse(events)
        self.touch.handle(self.finger(pygame.FINGERDOWN, 200, 200))
        events, tap, _ = self.touch.handle(self.finger(pygame.FINGERUP, 200, 130))
        self.assertFalse(tap)
        self.assertEqual(events[0].key, pygame.K_UP)

    def test_extra_fingers_do_not_interfere(self):
        self.touch.handle(self.finger(pygame.FINGERDOWN, 100, 100))
        events, tap, delta = self.touch.handle(self.finger(pygame.FINGERUP, 100, 100, 2))
        self.assertEqual((events, tap, delta), ([], False, (0, 0)))
