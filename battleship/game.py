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
        self.turn_player = None
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
        logger.info('both players are ready')
        # turn off the confirmation buttons
        for plyr in self.players.values():
            plyr.client.confirmation_button(on=False)
        # indicate turn
        self.turn_player.client.turn_led(on=True)
        self.turn_player.opponent.client.turn_led(on=False)

    def onturn(self, e):
        self.turn_player = self.turn_player.opponent
        self.turn_player.client.turn_led(on=True)
        self.turn_player.opponent.client.turn_led(on=False)

    def onover(self, e):
        logger.info('game over')

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
                self.game = Game(self.players)
                print('Thanks for playing')
                break

    def _handle_message(self, message):
        server_address, topic, params = message
        # determine player by unique port
        player = self.players[server_address[1]]
        # determine and call topic handler
        topic_handler = getattr(self, '_handle_message_{}'.format(topic))
        if not self.game.isstate('over'):
            topic_handler(player, params)
        else:
            logging.info('game is over, ignoring ui messages')

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
        if player is self.game.turn_player:
            board = player.opponent.board
            for i, param in enumerate(params):
                tile = board.tiles[i]
                if param == 1 and tile.can('fire'):
                    tile.fire()
                    if tile.isstate('miss'):
                        self.game.turn()
                    elif tile.isstate('hit'):
                        board._hits.add(i)
            # check if game is over
            if board.all_ships_destroyed():
                self.game.stop()
        player.opponent.publish_board()

    def _handle_message_ready(self, player, params):
        """Handles messages from the confirmation button."""
        if player.isstate('confirmation') and all(params):
            player.confirm()
            if self.game.turn_player is None:
                self.game.turn_player = player
        else:
            player.deny()
            if self.game.turn_player == player:
                self.game.turn_player = None
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
