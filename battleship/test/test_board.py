import unittest
from unittest.mock import Mock, MagicMock
from battleship.board import Tile


class TestTile(unittest.TestCase):
    def setUp(self):
        self.board = Mock()
        self.board.n = 5
        self.tile = Tile(2, 3, self.board)

    def test_init(self):
        import pdb; pdb.set_trace()
        self.assertEqual(self.tile.idx, 13, self.tile.idx)

    def test_set(self):
        self.assertTrue(self.tile.isstate('sea'), self.tile.current)
        self.tile.set()
        # assert board got a deck added
        self.assertTrue(self.tile.isstate('deck'), self.tile.current)
        self.tile.set()
        # assert board did not add a deck

    def test_reset(self):
        self.assertTrue(self.tile.isstate('sea'), self.tile.current)
        self.tile.reset()
        # assert that nothing changed with the board
        self.tile.set()
        self.assertTrue(self.tile.isstate('deck'), self.tile.current)
        self.tile.reset()
        self.assertTrue(self.tile.isstate('sea'), self.tile.current)
        # assert that deck was removed from the board
