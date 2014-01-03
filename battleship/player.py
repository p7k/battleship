import logging
import time
from itertools import permutations
from multiprocessing import Process, Queue
from pythonosc import dispatcher, osc_server, udp_client, osc_message_builder
from battleship import conf, board

logger = logging.getLogger(__name__)


class Game:
    def __init__(self):
        self.mq = Queue()
        # init the players (by server port)
        self.players = {}
        for player_conf in conf.PLAYERS[:2]:
            server_port = player_conf['server_address'][1]
            player = Player(game_queue=self.mq, **player_conf)
            self.players[server_port] = player
        # link opponents
        for player, opponent in permutations(self.players.values()):
            player.opponent = opponent

    def start(self):
        # clear boards
        for player in self.players.values():
            player.board = board.Board()
            player.publish_board()
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
        time.sleep(.05)
        topic_handler(player, params)

    def _handle_message_us(self, player, params):
        player.board.update(params)
        print(player.board)
        print(player.board.current)
        player.publish_board()

    def _handle_message_them(self, player, params):
        player.board.update(params)
        player.publish_board()


class Player:
    def __init__(self, game_queue, server_address, client_address):
        self.server = Server(server_address, game_queue)
        self.server.start()
        time.sleep(.1)
        self.client = Client(*client_address)

    def send_board(self):
        self.client.send_board(self.board, 'us')

    def send_board_to_opponent(self):
        self.opponent.client.send_board(self.board, 'them')

    def publish_board(self):
        self.send_board()
        self.send_board_to_opponent()


# client

def message_builder(topic):
    return osc_message_builder.OscMessageBuilder(conf.OSC_TOPICS[topic])


class Client(udp_client.UDPClient):
    def send(self, msg):
        """adds logging"""
        logger.debug('OSC send <%s> on <%s> %s',
                     (self._address, self._port), msg.address, msg.params)
        return super().send(msg)

    def send_board(self, board, topic):
        mb = message_builder(topic)
        for tile in board.tiles:
            mb.add_arg(conf.LEMUR_UI_BOARDS[topic][tile.current])
        msg = mb.build()
        self.send(msg)
        return msg


# server

class Server(Process):
    name = 'battleship_osc_server'
    daemon = True

    def __init__(self, server_address, queue):
        super().__init__()
        self.server_address = server_address
        # map all the topics to osc_addresses
        self.dispatcher = dispatcher.Dispatcher()
        for topic, osc_address in conf.OSC_TOPICS.items():
            self.dispatcher.map(osc_address, self._enqueue, osc_address, topic)
        self._queue = queue

    def _enqueue(self, args, *msg):
        osc_addr, topic = args
        logger.debug('OSC recv <%s> on <%s> %s',
                     self.server_address, osc_addr, msg)
        # time.sleep(.1)
        self._queue.put((self.server_address, topic, msg))

    def run(self):
        logger.info('starting osc server')
        server = osc_server.BlockingOSCUDPServer(self.server_address,
                                                 self.dispatcher)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        finally:
            server.server_close()
