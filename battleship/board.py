import logging
import bintrees
import fysom
import networkx
from battleship import midi, conf

logger = logging.getLogger(__name__)


class Tile(fysom.Fysom):
    """Belongs to a board"""
    symbols = dict(sea='~', deck='#', miss='o', hit='x')

    def __init__(self, midi_pitch_set=None):
        self.midi_pitch_set = midi_pitch_set
        self.midi_pitch = None
        super().__init__(
            dict(initial='sea',
                 events=(dict(name='on',   src='*',    dst='deck'),
                         dict(name='off',  src='*',    dst='sea'),
                         dict(name='fire', src='sea',  dst='miss'),
                         dict(name='fire', src='deck', dst='hit'))))

    def onsea(self, e):
        self.midi_stop()

    def ondeck(self, e):
        if not self.midi_pitch and self.midi_pitch_set:
            self.midi_pitch = self.midi_pitch_set.pop()
            logger.debug('midi pitch set: {}, len {}'.format(
                self.midi_pitch_set, len(self.midi_pitch_set)))
        if self.midi_pitch:
            midi.start(self.midi_pitch)

    def onhit(self, e):
        self.midi_crush()

    def midi_stop(self):
        if self.midi_pitch:
            midi.stop(self.midi_pitch)
            self.midi_pitch_set.add(self.midi_pitch)
            logger.debug('midi pitch set: {}, len {}'.format(
                self.midi_pitch_set, len(self.midi_pitch_set)))
            self.midi_pitch = None

    def midi_crush(self):
        if self.midi_pitch:
            midi.crush(self.midi_pitch)

    def midi_reset(self):
        if self.isstate('hit'):
            self.midi_crush()
        self.midi_stop()

    def __str__(self):
        return self.symbols[self.current]


class MisconfiguredShips(Exception):
    pass


class ShipTracker:
    def __init__(self, spec):
        self.spec = spec
        self._size_qty, self._sizes, = bintrees.FastAVLTree(), set()
        for size, qty in spec:
            assert size not in self._sizes, 'Duplicate ship size in spec'
            self._size_qty[size] = qty
            self._sizes.add(size)

    def _update_qty(self, size, delta):
        if size in self._sizes:
            self._size_qty[size] += delta

    def _has_bigger_ships(self, size):
        bigger_qtys = self._size_qty.value_slice(size + 1, None)
        return any(c > 0 for c in bigger_qtys)

    def add(self, size, group_sizes):
        logger.debug('composing {}-deck ship of {}'.format(size, group_sizes))
        n_ships_after = sum(self._size_qty.values()) - 1 + len(group_sizes)
        if n_ships_after < 0:
            raise MisconfiguredShips('all ships have already been started')
        qty = self._size_qty[size] if size in self._sizes else 0
        if not (qty > 0 or self._has_bigger_ships(size)):
            raise MisconfiguredShips('ships exhausted, no larger ships exist')
        self._update_qty(size, -1)
        for group_size in group_sizes:
            self._update_qty(group_size, 1)
        logger.debug('current ship tally: {}'.format(self._size_qty))

    def remove(self, size, ungroup_sizes):
        logger.debug(
            'decomposing {}-deck ship into of {}'.format(size, ungroup_sizes))
        n_ships_after = sum(self._size_qty.values()) + 1 - len(ungroup_sizes)
        if n_ships_after < 0:
            raise MisconfiguredShips('would try to add too many ships')
        self._update_qty(size, 1)
        for ungroup_size in ungroup_sizes:
            self.add(ungroup_size, [])
        logger.debug('current ship tally: {}'.format(self._size_qty))

    def is_complete(self):
        """Check if the configuration is complete and valid."""
        return all(value == 0 for value in self._size_qty.values())


class Board(fysom.Fysom):
    """Represents the game board.  Tiles are stored in a 1d tuple. """
    def __init__(self, n=conf.BOARD_SIZE, ship_spec=conf.SHIP_SPEC,
                 midi_pitch_set=None):
        self.n = n
        self.ship_tracker = ShipTracker(ship_spec)
        self.tiles = tuple(Tile(midi_pitch_set) for _ in range(n**2))
        self._decks = networkx.Graph()
        super().__init__(
            dict(initial='empty',
                 events=(dict(name='add',    src='empty',    dst='partial'),
                         dict(name='add',    src='partial',  dst='complete'),
                         dict(name='remove', src='complete', dst='partial'),
                         dict(name='remove', src='partial',  dst='empty'))))

    def _adjacent_tiles(self, i):
        n = self.n
        return (i - 1 if i % n != 0 else None,        # left edge
                i + n if i + n < n**2 else None,      # bottom edge
                i - n if i - n >= 0 else None,        # top edge
                i + 1 if (i + 1) % n != 0 else None)  # right edge

    def _find_ship_and_adjacents(self, i):
        """DFS work to find adjacent ships comprising the new larger ship."""
        ship, adj_decks, adj_ships = [i], [], []
        for adj_tile in self._adjacent_tiles(i):
            if adj_tile in self._decks:
                adj_decks.append(adj_tile)
                adj_ship = list(networkx.dfs_preorder_nodes(self._decks,
                                                            adj_tile))
                adj_ships.append(adj_ship)
                ship.extend(adj_ship)
        return sorted(ship), adj_decks, adj_ships

    def _is_valid_ship(self, tiles):
        """Mods of the tile indecies must be either all equal (vertical ship)
        or form a strict  n+0, n+1, .., n+k sequence (horizontal)."""
        if len(tiles) < 2:
            return True
        mods = [tile % self.n for tile in tiles]
        next_mod = iter(mods)
        next(next_mod)
        zip_mods = zip(iter(mods), next_mod)
        i, j = next(zip_mods)
        if i == j:
            is_valid = all(i == j for i, j in zip_mods)
        elif i + 1 == j:
            is_valid = all(i + 1 == j for i, j in zip_mods)
        else:
            is_valid = False
        return is_valid

    def onbeforeadd(self, e):
        i = e.args[0]
        # check if already added
        if i in self._decks:
            logger.debug('tile already a deck [%i], skipping...', i)
            return False
        # discover adjacent decks and ships
        ship, adj_decks, adj_ships = self._find_ship_and_adjacents(i)
        # check basic legality
        if not self._is_valid_ship(ship):
            logger.debug('invalid ship %s', ship)
            return False
        # track ship, check configuration
        try:
            self.ship_tracker.add(len(ship), list(map(len, adj_ships)))
        except MisconfiguredShips:
            return False
        # build graph
        self._decks.add_node(i)
        for adj_deck in adj_decks:
            self._decks.add_edge(i, adj_deck)
        # turn the tile on
        self.tiles[i].on()
        # check completeness
        if e.dst == 'complete' and not self.ship_tracker.is_complete():
            return False

    def onbeforeremove(self, e):
        i = e.args[0]
        # check if added
        if not i in self._decks:
            return False
        # remove from graph, early so that adjacent ships can be discovered
        self._decks.remove_node(i)
        # discover adjacent decks and ships
        ship, adj_decks, adj_ships = self._find_ship_and_adjacents(i)
        # track ship, check configuration
        try:
            self.ship_tracker.remove(len(ship), list(map(len, adj_ships)))
        except MisconfiguredShips:
            # rebuild the graph
            self._decks.add_node(i)
            for adj_deck in adj_decks:
                self._decks.add_edge(i, adj_deck)
            return False
        # turn the tile off
        self.tiles[i].off()
        # check emptiness
        if e.dst == 'empty' and self._decks:
            return False

    def place_tiles(self, switches):
        for i, switch in enumerate(switches):
            switch = int(switch)
            if switch == 1 and self.can('add'):
                self.add(i)
            elif switch == 0 and self.can('remove'):
                self.remove(i)

    def all_ships_destroyed(self):
        return all(self.tiles[i].isstate('hit') for i in self._decks)

    def __str__(self):
        edge = '|{}|'.format('-' * (self.n*2 + 1))
        rows = []
        for i in range(0, self.n**2, self.n):
            row = '| {} |'.format(' '.join(map(str, self.tiles[i:i+self.n])))
            rows.append(row)
        return '{edge}\n{rows}\n{edge}'.format(edge=edge, rows='\n'.join(rows))
