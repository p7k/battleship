import logging
from fysom import Fysom
import networkx as nx
from battleship import midi

logging.basicConfig(
    format='%(asctime)-24s%(levelname)-10s%(name)-25s%(message)s',
    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Tile(Fysom):
    """Belongs to a board"""
    symbols = dict(sea='~', deck='#', miss='o', hit='x')

    def __init__(self, midi_pitch=None):
        self.midi_pitch = midi_pitch
        super().__init__(
            dict(initial='sea',
                 events=(dict(name='on',   src='*',    dst='deck'),
                         dict(name='off', src='*',    dst='sea'),
                         dict(name='fire',  src='sea',  dst='miss'),
                         dict(name='fire',  src='deck', dst='hit'))))

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


def process_ship_specs(specs):
    """Validates, sums up the decks and freezes the spec:
        - Return:   tuple(frozenset(specs), deck_sum)
    """
    sizes_seen = set()
    deck_sum = 0
    for size, qty in specs:
        assert size not in sizes_seen, 'Duplicate ship size in specs'
        deck_sum += size * qty
    return frozenset(specs), deck_sum


class Board(Fysom):
    """Represents the game board.
    Tiles are stored in a 1D tuple structure.
    """
    def __init__(self, n, ship_specs):
        # spec validation
        self.ship_specs, self.n_decks = process_ship_specs(ship_specs)
        assert n**2 > self.n_decks * 2, 'Ships occupy too much of the board.'
        # main storage
        self.n, self._tiles = n, tuple(Tile() for _ in range(n**2))
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

    def _find_ship(self, i):
        return tuple(nx.dfs_preorder_nodes(self._decks, i))

    def _is_valid_ship(self, tiles):
        """Checks legality of a tile group by running a check on the algebraic
        series.  A group should have an interval of n or 1 to be a proper
        series.  Otherwise, the series and actual sums won't be equal."""
        return len(tiles) * (min(tiles) + max(tiles)) // 2 == sum(tiles)

    def onbeforeadd(self, e):
        i = e.args[0]
        # discover adjacent decks and ships
        ship, adj_decks, adj_ships = [i], [], []
        for adj_tile in self._adjacent_tiles(i):
            if adj_tile in self._decks:
                adj_decks.append(adj_tile)
                adj_ship = self._find_ship(adj_tile)
                adj_ships.append(adj_ship)
                ship.extend(adj_ship)
        # check basic legality
        if not self._is_valid_ship(ship):
            return False
        # build graph
        self._decks.add_node(i)
        for adj_deck in adj_decks:
            self._decks.add_edge(i, adj_deck)
        # turn the tile on
        self._tiles[i].on()
        # check completeness
        if e.dst == 'complete' and len(self._decks) < self.n_decks:
            return False

    def onbeforeremove(self, e):
        self._decks.remove_node(e.i)
        self._tiles[e.i].off()
        if e.dst == 'empty' and self._decks:
            return False

    def oncomplete(self, e):
        ships = nx.connected_components(self._decks)
        # validate
        freq = dict()
        for ship in ships:
            ship_size = len(ship)
            freq.setdefault(ship_size, 0)
            freq[ship_size] += 1
        if ships and all(cfg in self.ship_cfg for cfg in freq.items()):
            print('board complete and valid')
            if self.player:
                self.player.valid()

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
            row = '| {} |'.format(' '.join(map(str, self._tiles[i:i+self.n])))
            rows.append(row)
        return '{edge}\n{rows}\n{edge}'.format(edge=edge, rows='\n'.join(rows))
