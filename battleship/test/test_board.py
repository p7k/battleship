import unittest
from battleship.board import Tile


class TestTile(unittest.TestCase):
    def test_fsm(self):
        tile = Tile(0, 0)
        self.assertTrue(tile.isstate('sea'))
