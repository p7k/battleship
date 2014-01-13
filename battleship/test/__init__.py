import unittest


class BattleTest(unittest.TestCase):
    def assert_tile_state(self, tile, state):
        self.assertTrue(tile.isstate(state),
                        'current state: {}'.format(tile.current))
