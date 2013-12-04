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


class Ship(Fysom):
    """collection of tiles | specify number of decks"""

    def __init__(self, tiles):
        for tile in tiles:
            assert tile.isstate('deck'), (str(tile), tile.current)
            tile.ship = self
        self.tiles = set(tiles)
        super().__init__(
            dict(initial='ok', final='sunken',
                 events=(dict(name='fire', src='ok',      dst='damaged'),
                         dict(name='fire', src='damaged', dst='sunken'))))

    def onleavedamaged(self, e):
        if not all(t.isstate('hit') for t in self.tiles):
            return False

    def onsunken(self, e):
        print('ship sunk, stop the noise')


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
    def __init__(self, n, ship_specs, player=None):
        # spec validation
        self.ship_specs, self.n_decks = process_ship_specs(ship_specs)
        assert n**2 > self.n_decks * 2, 'Ships occupy too much of the board.'
        # main storage
        self.n, self._tiles = n, tuple(Tile() for _ in range(n**2))
        # keeping track of decks
        self._decks, self._decks_hit = set(), set()
        # ship placement fsm
        super().__init__(
            dict(initial='empty',
                 events=(dict(name='add',    src='empty',    dst='partial'),
                         dict(name='add',    src='partial',  dst='complete'),
                         dict(name='remove', src='complete', dst='partial'),
                         dict(name='remove', src='partial',  dst='empty'))))
        # TODO ?
        self.player = player

    def fire(self, i):
        tile = self.tile_1d(i)
        tile.fire()
        if tile.isstate('hit'):
            self.hit_decks.add(tile)
            self.board.player.game.stop()

    def onbeforeadd(self, e):
        assert e.i not in self._decks, 'Deck already added.'
        self._decks.add(e.i)
        self._tiles[e.i].on()
        if e.dst == 'complete' and len(self._decks) < self.n_decks:
            return False

    def onbeforeremove(self, e):
        tile = self.tile_1d(e.i)
        tile.reset()
        self.decks.remove(tile)
        if e.dst == 'empty' and self.decks:
            return False

    def oncomplete(self, e):
        ships = self._detect_ships()
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

    def onpartial(self, e):
        if self.player:
            self.player.invalid()

    def _detect_ships(self):
        graph = nx.Graph()
        # all decks are nodes
        graph.add_nodes_from(self.decks)
        # edges exist between proper neighbors
        for deck in self.decks:
            k = self.tiles[max(deck.i - 1, 0)][deck.j]
            j = self.tiles[min(deck.i + 1, self.n - 1)][deck.j]
            h = self.tiles[deck.i][max(deck.j - 1, 0)]
            l = self.tiles[deck.i][min(deck.j + 1, self.n - 1)]
            # if has both hor and ver neigbors - wrong
            # TODO rewrite
            hor_edges = False
            for adj in (h, l):
                if not adj == deck and adj.isstate('deck'):
                    hor_edges = True
                    graph.add_edge(deck, adj)
            for adj in (j, k):
                if not adj == deck and adj.isstate('deck'):
                    if hor_edges:
                        return []
                    graph.add_edge(deck, adj)
        return nx.connected_components(graph)

    def __str__(self):
        edge = '|{}|'.format('-' * (self.n*2 + 1))
        rows = []
        for i in range(0, self.n**2, self.n):
            row = '| {} |'.format(' '.join(map(str, self._tiles[i:i+self.n])))
            rows.append(row)
        return '{edge}\n{rows}\n{edge}'.format(edge=edge, rows='\n'.join(rows))
