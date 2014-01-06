import unittest
from itertools import chain
from battleship import board


class TestTile(unittest.TestCase):
    def setUp(self):
        self.tile = board.Tile()

    def test_init(self):
        self.assertTrue(self.tile.isstate('sea'), self.tile.current)

    def test_set(self):
        self.tile.on()
        self.assertTrue(self.tile.isstate('deck'), self.tile.current)
        self.tile.on()
        self.assertTrue(self.tile.isstate('deck'), self.tile.current)

    def test_reset(self):
        self.tile.off()
        self.assertTrue(self.tile.isstate('sea'), self.tile.current)
        self.tile.on()
        self.assertTrue(self.tile.isstate('deck'), self.tile.current)
        self.tile.off()
        self.assertTrue(self.tile.isstate('sea'), self.tile.current)

    def test_hit(self):
        # TODO test midi with mock
        self.tile.on()
        self.tile.fire()
        self.assertTrue(self.tile.isstate('hit'), self.tile.current)

    def test_miss(self):
        self.tile.fire()
        self.assertTrue(self.tile.isstate('miss'), self.tile.current)


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = board.Board(n=5, ship_spec=[(4, 1), (3, 1),
                                                 (2, 1), (1, 2)],
                                 midi_pitch_set=set(range(36, 57)))

    def test_init(self):
        self.assertEqual(len(self.board.tiles), 25)
        self.assertTrue(self.board.isstate('empty'))

    def test_add_horizontal_ship(self):
        # ship
        for i in [5, 6, 7]:
            self.board.add(i)
            self.assertTrue(self.board.tiles[i].isstate('deck'), i)
        # invalids
        for i in chain([0, 1, 2], [10, 11, 12]):
            self.board.add(i)
            self.assertTrue(self.board.tiles[i].isstate('sea'), i)

    def test_add_vertical_ship(self):
        # ship
        for i in [1, 6, 11]:
            self.board.add(i)
            self.assertTrue(self.board.tiles[i].isstate('deck'), i)
        # invalids
        for i in chain([0, 5, 10], [2, 7, 12]):
            self.board.add(i)
            self.assertTrue(self.board.tiles[i].isstate('sea'), i)

    def test_add_invalid_ship_by_connecting_two_others(self):
        for i in chain([0, 1], [11]):
            self.board.add(i)
            self.assertTrue(self.board.tiles[i].isstate('deck'), i)
        self.board.add(6)
        self.assertTrue(self.board.tiles[6].isstate('sea'))

    def test_add_snake_ship_horizontal(self):
        """wraps around, so defeats the simple arithmetic sum check"""
        for i in chain([2, 3, 4], [5, 6]):
            self.board.add(i)
            self.assertTrue(self.board.tiles[i].isstate('deck'), i)
        self.board.add(7)
        self.assertTrue(self.board.tiles[7].isstate('sea'), 7)

    def test_add_snake_ship_vertical(self):
        """wraps around, so defeats the simple arithmetic sum check"""
        for i in [11, 16, 21, 2, 7]:
            self.board.add(i)
            self.assertTrue(self.board.tiles[i].isstate('deck'), i)
        self.board.add(12)
        self.assertTrue(self.board.tiles[12].isstate('sea'), 12)

    def test_add_all_ships(self):
        # start with an empty board
        self.assertTrue(self.board.isstate('empty'))
        # add all but one 1-deck ship
        for i in chain([0, 5, 10, 15], [21, 22, 23], [14, 19], [8]):
            self.board.add(i)
            self.assertTrue(self.board.tiles[i].isstate('deck'), i)
            self.assertTrue(self.board.isstate('partial'), i)
        # last 1-deck ship, should make board complete
        self.board.add(2)
        self.assertTrue(self.board.isstate('complete'))
