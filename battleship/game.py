import itertools
import logging
import multiprocessing
import queue
import time
import fysom
from battleship import board, conf, osc

logger = logging.getLogger(__name__)


class Player(fysom.Fysom):
    def __init__(self, game_queue, server_address, client_address):
        self.server = osc.Server(server_address, game_queue)
        self.server.start()
        time.sleep(.2)
        self.client = osc.Client(*client_address)
        super().__init__(
            dict(initial='setup',
                 events=(dict(name='prompt', src='setup', dst='confirmation'),
                         dict(name='confirm', src='confirmation', dst='ready'),
                         dict(name='deny', src='*', dst='setup'))))

    def onready(self, e):
        logger.info('player ready')

    def onsetup(self, e):
        logger.debug('turning off prompt button')
        self.client.confirmation_button(on=False)
        self.client.confirmation_value(on=False)
        self.client.turn_led(on=False)

    def onconfirmation(self, e):
        logger.debug('turning on prompt button')
        self.client.confirmation_value(on=False)
        self.client.confirmation_button(on=True)

    def send_board(self):
        self.client.send_board(self.board, 'us')

    def send_board_to_opponent(self):
        self.opponent.client.send_board(self.board, 'them')

    def publish_board(self):
        self.send_board()
        self.send_board_to_opponent()


class Game(fysom.Fysom):
    def __init__(self, players):
        logger.info('starting new game')
        self.players = players
        self.turn_player = None
        self._reset_players()
        super().__init__(
            dict(initial='setup', final='over',
                 events=(dict(name='play', src='setup', dst='p1'),
                         dict(name='turn', src='p1',    dst='p2'),
                         dict(name='turn', src='p2',    dst='p1'),
                         dict(name='stop', src='*',     dst='over'))))

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
        # stop all decks, uncrush all hits
        for plyr in self.players.values():
            for tile in plyr.board.tiles:
                tile.midi_reset()

    def _reset_players(self):
        logger.debug('resetting the boards and ui')
        midi_pitch_set = set(conf.MIDI_PITCH_RANGE)
        for plyr in self.players.values():
            plyr.board = board.Board(midi_pitch_set=midi_pitch_set)
            plyr.deny()
            plyr.publish_board()


class GameManager:
    def __init__(self, players_conf=conf.PLAYERS):
        self.mq = multiprocessing.Queue()
        self.last_game_ended = None
        # init the players (by server port)
        self.players = {}
        for player_conf in players_conf[:2]:
            server_port = player_conf['server_address'][1]
            plyr = Player(game_queue=self.mq, **player_conf)
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
                logging.info('game timed out after {} sec, new game'.format(
                    conf.GAME_TIMEOUT))
                self.game.stop()
                self.game = Game(self.players)
            except KeyboardInterrupt:
                self.game.stop()
                self.game = Game(self.players)
                print('Stokrotka!!!')
                break

    def _handle_message(self, message):
        server_address, topic, params = message
        # determine player by unique port
        player = self.players[server_address[1]]
        # determine and call topic handler
        topic_handler = getattr(self, '_handle_message_{}'.format(topic))
        if self.game.isstate('over'):
            if time.time() - self.last_game_ended > conf.IGNORE_TIME_GAME_OVER:
                self.game = Game(self.players)
            else:
                logging.info('game is over, ignoring ui messages')
        else:
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
        if player is self.game.turn_player:
            board = player.opponent.board
            for i, param in enumerate(params):
                tile = board.tiles[i]
                if param == 1 and tile.can('fire'):
                    tile.fire()
                    if tile.isstate('miss'):
                        self.game.turn()
                    # important to make sure that we don't allow multifire
                    break
            # check if game is over
            if board.all_ships_destroyed():
                self.game.stop()
                self.last_game_ended = time.time()
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
