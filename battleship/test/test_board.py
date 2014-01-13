from itertools import chain
from battleship import board
from battleship import test


class TestTile(test.BattleTest):
    def setUp(self):
        self.tile = board.Tile()

    def assert_tile_state(self, state):
        super().assert_tile_state(self.tile, state)

    def test_init(self):
        self.assert_tile_state('sea')

    def test_set(self):
        self.tile.on()
        self.assert_tile_state('deck')
        self.tile.on()
        self.assert_tile_state('deck')

    def test_reset(self):
        self.tile.off()
        self.assert_tile_state('sea')
        self.tile.on()
        self.assert_tile_state('deck')
        self.tile.off()
        self.assert_tile_state('sea')

    def test_hit(self):
        # TODO test midi with mock
        self.tile.on()
        self.tile.fire()
        self.assert_tile_state('hit')

    def test_miss(self):
        self.tile.fire()
        self.assert_tile_state('miss')


class TestBoard(test.BattleTest):
    def setUp(self):
        self.board = board.Board(n=5, ship_spec=[(4, 1), (3, 1),
                                                 (2, 1), (1, 2)],
                                 midi_pitch_set=set(range(36, 57)))

    def assert_tile_state(self, idx, state):
        super().assert_tile_state(self.board.tiles[idx], state)

    def test_init(self):
        self.assertEqual(len(self.board.tiles), 25)
        self.assertTrue(self.board.isstate('empty'))

    def test_add_horizontal_ship(self):
        # ship
        for i in [5, 6, 7]:
            self.board.add(i)
            self.assert_tile_state(i, 'deck')
        # invalids
        for i in chain([0, 1, 2], [10, 11, 12]):
            self.board.add(i)
            self.assert_tile_state(i, 'sea')

    def test_add_vertical_ship(self):
        # ship
        for i in [1, 6, 11]:
            self.board.add(i)
            self.assert_tile_state(i, 'deck')
        # invalids
        for i in chain([0, 5, 10], [2, 7, 12]):
            self.board.add(i)
            self.assert_tile_state(i, 'sea')

    def test_add_invalid_ship_by_connecting_two_others(self):
        for i in chain([0, 1], [11]):
            self.board.add(i)
            self.assert_tile_state(i, 'deck')
        # bad seed
        i = 6
        self.board.add(i)
        self.assert_tile_state(i, 'sea')

    def test_add_snake_ship_horizontal(self):
        """wraps around, so defeats the simple arithmetic sum check"""
        for i in chain([2, 3, 4], [5, 6]):
            self.board.add(i)
            self.assert_tile_state(i, 'deck')
        # bad seed
        i = 7
        self.board.add(i)
        self.assert_tile_state(i, 'sea')

    def test_add_snake_ship_vertical(self):
        """wraps around, so defeats the simple arithmetic sum check"""
        for i in [11, 16, 21, 2, 7]:
            self.board.add(i)
            self.assert_tile_state(i, 'deck')
        # bad seed
        i = 12
        self.board.add(i)
        self.assert_tile_state(i, 'sea')

    def test_add_all_ships(self):
        # start with an empty board
        self.assertTrue(self.board.isstate('empty'))
        # add all but one 1-deck ship
        for i in chain([0, 5, 10, 15], [21, 22, 23], [14, 19], [8]):
            self.board.add(i)
            self.assert_tile_state(i, 'deck')
            self.assertTrue(self.board.isstate('partial'), i)
        # last 1-deck ship, should make board complete
        i = 2
        self.board.add(i)
        self.assert_tile_state(i, 'deck')
        self.assertTrue(self.board.isstate('complete'))
