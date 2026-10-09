import importlib.util
import random
import unittest

from game.rendering.animation_renderer import LoopingAnimation


class LoopingAnimationTests(unittest.TestCase):
    def test_advances_and_wraps(self):
        animation = LoopingAnimation(["a", "b", "c"], fps=2.0)
        animation.update(1.1)
        self.assertEqual("c", animation.current_frame)
        animation.update(0.5)
        self.assertEqual("a", animation.current_frame)

    def test_reset_restores_first_frame(self):
        animation = LoopingAnimation(["a", "b"], fps=2.0)
        animation.update(0.6)
        animation.reset()
        self.assertEqual("a", animation.current_frame)
        self.assertEqual(0.0, animation.elapsed)


@unittest.skipUnless(importlib.util.find_spec("pygame"), "pygame is not installed")
class Scene02ShootingStarTests(unittest.TestCase):
    def setUp(self):
        from game.rendering.scene02_renderer import Scene02Renderer
        self.renderer_class = Scene02Renderer

    def make_renderer(self):
        class FakeAssets:
            def image(self, key, path):
                return path

        config = {
            "presentation": {
                "shooting_star": {
                    "fps": 10.0,
                    "min_delay": 1.0,
                    "max_delay": 1.0,
                    "position": [310, 105],
                }
            }
        }
        return self.renderer_class(FakeAssets(), config, rng=random.Random(1234))

    def test_delay_only_counts_down_while_sky_is_visible(self):
        renderer = self.make_renderer()
        renderer.update(2.0, "river")
        self.assertFalse(renderer.shooting_star_active)
        self.assertEqual(1.0, renderer.shooting_star_delay)

        renderer.update(1.0, "sky")
        self.assertTrue(renderer.shooting_star_active)
        self.assertEqual(0, renderer.shooting_star_frame)

    def test_active_event_finishes_after_looking_away(self):
        renderer = self.make_renderer()
        renderer.update(1.0, "sky")
        self.assertTrue(renderer.shooting_star_active)

        renderer.update(1.3, "river")
        self.assertFalse(renderer.shooting_star_active)
        self.assertEqual(0, renderer.shooting_star_frame)
        self.assertEqual(1.0, renderer.shooting_star_delay)

    def test_authored_position_comes_from_config(self):
        renderer = self.make_renderer()
        self.assertEqual((310, 105), renderer.shooting_star_pos)


if __name__ == "__main__":
    unittest.main()
