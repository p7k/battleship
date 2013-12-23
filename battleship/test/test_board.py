import unittest
from itertools import chain
from battleship import board


class TestTile(unittest.TestCase):
    def setUp(self):
        self.tile = board.Tile(midi_pitch=36)

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
        self.board = board.Board(n=5,
                                 ship_specs=((4, 1), (3, 1), (2, 1), (1, 2)))

    def test_init(self):
        self.assertEqual(len(self.board._tiles), 25)
        self.assertEqual(self.board.n_decks, 11)
        self.assertTrue(self.board.isstate('empty'))

    def test_add_horizontal_ship(self):
        # ship
        for i in [5, 6, 7]:
            self.board.add(i=i)
            self.assertTrue(self.board._tiles[i].isstate('deck'), i)
        # invalids
        for i in chain([0, 1, 2], [10, 11, 12]):
            self.board.add(i=i)
            self.assertTrue(self.board._tiles[i].isstate('sea'), i)

    def test_add_vertical_ship(self):
        # ship
        for i in [1, 6, 11]:
            self.board.add(i=i)
            self.assertTrue(self.board._tiles[i].isstate('deck'), i)
        # invalids
        for i in chain([0, 5, 10], [2, 7, 12]):
            self.board.add(i=i)
            self.assertTrue(self.board._tiles[i].isstate('sea'), i)

    def test_add_invalid_ship_by_connecting_two_others(self):
        for i in chain([0, 1], [11]):
            self.board.add(i=i)
            self.assertTrue(self.board._tiles[i].isstate('deck'), i)
        self.board.add(i=6)
        self.assertTrue(self.board._tiles[6].isstate('sea'))

    def test_add_all_ships(self):
        # start with an empty board
        self.assertTrue(self.board.isstate('empty'))
        # add all but one 1-deck ship
        for i in chain([0, 5, 10, 15], [21, 22, 23], [14, 19], [8]):
            self.board.add(i=i)
            self.assertTrue(self.board._tiles[i].isstate('deck'), i)
            self.assertTrue(self.board.isstate('partial'), i)
        # last 1-deck ship, should make board complete
        # self.board.add(i=2)
        # self.assertTrue(self.board.isstate('complete'))
        print(self.board)
        print(self.board._ships)
