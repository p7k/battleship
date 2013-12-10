import unittest
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

    def test_add(self):
        # 4-deck
        self.board.add(i=0)
        self.assertTrue(self.board.isstate('partial'))
        self.board.add(i=5)
        self.board.add(i=10)
        self.board.add(i=15)
        # 3-deck
        self.board.add(i=21)
        self.board.add(i=22)
        self.board.add(i=23)
        # 2-deck
        self.board.add(i=14)
        self.board.add(i=19)
        # 1-deck
        self.board.add(i=11)
        self.assertTrue(self.board.isstate('partial'))
        # 1-deck
        # self.board.add(i=2)
        print(self.board)

    def test_add_dup(self):
        pass

    # def test_print(self):
    #     self.board._tiles[1].on()
    #     self.board._tiles[5].on()
    #     self.board._tiles[5].fire()
    #     self.board._tiles[23].fire()
    #     print()
    #     print(self.board)
