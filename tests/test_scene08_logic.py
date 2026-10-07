import unittest

class Scene08InvariantTests(unittest.TestCase):
    def test_approach_update_is_monotonic(self):
        sensitivity=0.0018
        approach=0.35
        for dy in (20,-50,10,-100,400):
            before=approach
            if dy > 0:
                approach=min(1.0, approach+dy*sensitivity)
            self.assertGreaterEqual(approach,before)
            self.assertLessEqual(approach,1.0)
