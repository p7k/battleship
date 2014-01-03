import logging
from fysom import Fysom, FysomError
import networkx as nx
import bintrees
from battleship import midi, conf

logger = logging.getLogger(__name__)


class Tile(Fysom):
    """Belongs to a board"""
    symbols = dict(sea='~', deck='#', miss='o', hit='x')

    def __init__(self, midi_pitch=None):
        self.midi_pitch = midi_pitch
        super().__init__(
            dict(initial='sea',
                 events=(dict(name='on',   src='*',    dst='deck'),
                         dict(name='off',  src='*',    dst='sea'),
                         dict(name='fire', src='sea',  dst='miss'),
                         dict(name='fire', src='deck', dst='hit'))))

    def onsea(self, e):
        if self.midi_pitch:
            midi.stop(self.midi_pitch)

    def ondeck(self, e):
        if self.midi_pitch:
            midi.start(self.midi_pitch)

    def onhit(self, e):
        if self.midi_pitch:
            midi.crush(self.midi_pitch)

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
        if sum(self._size_qty.values()) + len(group_sizes) < 1:
            raise MisconfiguredShips('all ships have already been started')
        qty = self._size_qty[size] if size in self._sizes else 0
        if not (qty > 0 or self._has_bigger_ships(size)):
            raise MisconfiguredShips('ships exhausted, no larger ships exist')
        self._update_qty(size, -1)
        for group_size in group_sizes:
            self._update_qty(group_size, 1)

    def remove(self, size, ungroup_sizes):
        self._update_qty(size, 1)

    def is_complete(self):
        """Check if the configuration is complete and valid."""
        return all(value == 0 for value in self._size_qty.values())


class Board(Fysom):
    """Represents the game board.
    Tiles are stored in a 1D tuple structure.
    """
    def __init__(self, n=conf.BOARD_SIZE, ship_spec=conf.SHIP_SPEC):
        # spec validation
        self.ship_tracker = ShipTracker(ship_spec)
        # main storage
        self.n, self.tiles = n, tuple(Tile() for _ in range(n**2))
        # graph of decks
        self._decks = nx.Graph()
        # keeping track of hit decks
        self._hits = set()
        # ship placement fsm
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
                adj_ship = list(nx.dfs_preorder_nodes(self._decks, adj_tile))
                adj_ships.append(adj_ship)
                ship.extend(adj_ship)
        return ship, adj_decks, adj_ships

    def _is_valid_ship(self, tiles):
        """Checks legality of a tile group by running a check on the algebraic
        series.  A group should have an interval of n or 1 to be a proper
        series.  Otherwise, the series and actual sums won't be equal."""
        return len(tiles) * (min(tiles) + max(tiles)) // 2 == sum(tiles)

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
        # try:
        #     self.ship_tracker.add(len(ship), list(map(len, adj_ships)))
        # except MisconfiguredShips:
        #     return False
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
        # turn the tile off
        self.tiles[i].off()
        # check emptiness
        if e.dst == 'empty' and self._decks:
            return False

    def update(self, switches):
        for i, switch in enumerate(switches):
            try:
                if int(switch):
                    self.add(i)
                else:
                    self.remove(i)
            except FysomError:
                break

    def fire(self, i):
        tile = self.tile_1d(i)
        tile.fire()
        if tile.isstate('hit'):
            self._hits.add(tile)
            self.board.player.game.stop()

    def __str__(self):
        edge = '|{}|'.format('-' * (self.n*2 + 1))
        rows = []
        for i in range(0, self.n**2, self.n):
            row = '| {} |'.format(' '.join(map(str, self.tiles[i:i+self.n])))
            rows.append(row)
        return '{edge}\n{rows}\n{edge}'.format(edge=edge, rows='\n'.join(rows))
