import multiprocessing
from itertools import permutations
from battleship import board, conf, player


class Game:
    def __init__(self, players):
        self.players = players
        self._reset_boards()

    def _reset_boards(self):
        for plyr in self.players.values():
            plyr.board = board.Board()
            plyr.publish_board()


class GameManager:
    def __init__(self, players_conf=conf.PLAYERS):
        self.mq = multiprocessing.Queue()
        # init the players (by server port)
        self.players = {}
        for player_conf in players_conf[:2]:
            server_port = player_conf['server_address'][1]
            plyr = player.Player(game_queue=self.mq, **player_conf)
            self.players[server_port] = plyr
        # link opponents
        for plyr, opponent in permutations(self.players.values()):
            plyr.opponent = opponent

        self.on = False

    def start(self):
        self.game = Game(self.players)
        # start mq loop
        while True:
            try:
                message = self.mq.get(timeout=conf.GAME_TIMEOUT)
                self._handle_message(message)
            except KeyboardInterrupt:
                break

    def _handle_message(self, message):
        server_address, topic, params = message
        # determine player by unique port
        player = self.players[server_address[1]]
        # determine and call topic handler
        topic_handler = getattr(self, '_handle_message_{}'.format(topic))
        topic_handler(player, params)

    def _handle_message_us(self, player, params):
        """Handles messages from player's own board. (just during setup)"""
        if not self.on:
            player.board.place_tiles(params)
        print(player.board)
        print(player.board.current)
        player.send_board()

    def _handle_message_them(self, player, params):
        """Handles messages from player's monitor board. (game play)"""
        if any(params):
            self.on = True
        player.opponent.board.attack_tiles(params)
        player.opponent.publish_board()
