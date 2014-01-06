import logging
import itertools
import multiprocessing
import queue
import fysom
from battleship import board, conf, player

logger = logging.getLogger(__name__)


class Game(fysom.Fysom):
    def __init__(self, players):
        logger.info('starting new game')
        self.players = players
        self._reset_boards()
        super().__init__(
            dict(initial='setup', final='over',
                 events=(dict(name='play', src='setup',      dst='p1'),
                         dict(name='turn', src='p1',         dst='p2'),
                         dict(name='turn', src='p2',         dst='p1'),
                         dict(name='stop', src=('p1', 'p2'), dst='over'))))

    def onbeforeplay(self, e):
        if not all(plyr.isstate('ready') for plyr in self.players.values()):
            return False

    def _reset_boards(self):
        logger.debug('resetting the boards and ui')
        for plyr in self.players.values():
            plyr.board = board.Board()
            plyr.publish_board()
            plyr.client.turn_led(on=False)


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
        for plyr, opponent in itertools.permutations(self.players.values()):
            plyr.opponent = opponent

    def start(self):
        self.game = Game(self.players)
        # start mq loop
        while True:
            try:
                message = self.mq.get(timeout=conf.GAME_TIMEOUT)
                self._handle_message(message)
            except queue.Empty:
                self.game = Game(self.players)
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
        print(self.game.current, player.current)
        if self.game.isstate('setup') and \
                player.current in set(['setup', 'confirmation']):
            player.board.place_tiles(params)
        player.send_board()
        # confirmation
        if player.board.isstate('partial'):
            player.deny()
        if player.board.isstate('complete') and player.can('prompt'):
            player.prompt()

    def _handle_message_them(self, player, params):
        """Handles messages from player's monitor board. (game play)"""
        player.opponent.board.attack_tiles(params)
        player.opponent.publish_board()

    def _handle_message_ready(self, player, params):
        """Handles messages from the confirmation button."""
        if player.isstate('confirmation') and all(params):
            player.confirm()
        else:
            player.deny()
        # confirmation
        if player.board.isstate('partial'):
            player.deny()
        if player.board.isstate('complete') and player.can('prompt'):
            player.prompt()
        # attempt to start the game
        self.game.play()


def run():
    game_manager = GameManager()
    game_manager.start()
