from fysom import Fysom
import networkx as nx
from battleship import midi


class Tile(Fysom):
    """Belongs to a board and a ship"""
    symbols = dict(sea='~', deck='#', miss='o', hit='x')

    def __init__(self, i, j, board=None, ship=None):
        self.i, self.j = i, j
        self.board = board
        self.ship = ship
        super().__init__(
            dict(initial='sea',
                 events=(dict(name='set',   src=('sea', 'deck'), dst='deck'),
                         dict(name='reset', src=('deck', 'sea'), dst='sea'),
                         dict(name='fire',  src='sea',           dst='miss'),
                         dict(name='fire',  src='deck',          dst='hit'))))

    def onbeforeset(self, e):
        """checks to see if the board is complete"""
        if self.board:
            if self.board.isstate('complete'):
                return False

    def onset(self, e):
        """actually adds to board decks"""
        if self.board:
            self.board.add(tile=self)

    def onreset(self, e):
        """removes from board decks"""
        if self.board and self in self.board.decks:
            self.board.decks.remove(self)
            self.board.remove()

    def ondeck(self, e):
        """start sfx"""
        print('added a deck, start playing a loop')
        if self.board:
            midi.start(self.board.idx(self) + 36)

    def onsea(self, e):
        """stop sfx"""
        if self.board:
            midi.stop(self.board.idx(self) + 36)

    def onhit(self, e):
        """notifies the ship"""
        print('got hit, crushing the loop')
        if self.ship:
            self.ship.fire()
        if self.board:
            self.board.hit_decks.add(self)
            self.board.player.game.stop()
            midi.crush(self.board.idx(self) + 36)

    def __str__(self):
        return 'Tile({0},{1})'.format(self.i, self.j)

    def __repr__(self):
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


class Board(Fysom):
    """keeps track of tiles"""

    def __init__(self, n, ship_cfg, player=None):
        self.n = n
        self.tiles = tuple(
            tuple(Tile(i, j, board=self) for j in range(n)) for i in range(n))
        self.total_decks = 0
        self.decks = set()
        self.hit_decks = set()
        self.ship_cfg = ship_cfg
        for n_decks, qty in self.ship_cfg:
            self.total_decks += n_decks * qty
        self.player = player
        super().__init__(
            dict(initial='partial', final='valid',
                 events=(dict(name='add',    src='partial',  dst='complete'),
                         dict(name='remove', src=('partial', 'complete'),
                              dst='partial'))))

    def onbeforeadd(self, e):
        if not len(self.decks) < self.total_decks:
            raise False
        self.decks.add(e.tile)
        if len(self.decks) < self.total_decks:
            return False

    def oncomplete(self, e):
        ships_to_pack = self._detect_ships()
        # validate
        freq = dict()
        for ship_to_pack in ships_to_pack:
            freq.setdefault(len(ship_to_pack), []).append(0)
        if ships_to_pack and all((k, len(freq[k])) in self.ship_cfg for k in freq):
            print('board complete and valid')
            if self.player:
                self.player.valid()

    def onpartial(self, e):
        if self.player:
            self.player.invalid()

    def tile_1d(self, i):
        return self.tiles[i // self.n][i % self.n]

    def idx(self, tile):
        return tile.i * self.n + tile.j

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
        edge = '|{}|'.format('-' * (self.n * 2 + 1))
        rows = '\n'.join(
            '| {} |'.format(' '.join(map(repr, row))) for row in self.tiles)
        return '{edge}\n{rows}\n{edge}'.format(**locals())
