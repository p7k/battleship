import logging
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

        self.on = False

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


class Player:
    def __init__(self, game_queue, server_address, client_address):
        self.server = Server(server_address, game_queue)
        self.server.start()
        self.client = Client(*client_address)

    def send_board(self):
        self.client.send_board(self.board, 'us')

    def send_board_to_opponent(self):
        self.opponent.client.send_board(self.board, 'them')

    def publish_board(self):
        self.send_board()
        self.send_board_to_opponent()


class Client(udp_client.UDPClient):
    def __init__(self, host, port, topic_mapping=conf.OSC_TOPICS):
        super().__init__(host, port)
        self.topic_mapping = topic_mapping

    def message_builder(self, topic):
        osc_address = self.topic_mapping[topic][1]
        return osc_message_builder.OscMessageBuilder(osc_address)

    def send(self, msg):
        """adds logging"""
        logger.debug('OSC send <%s> on <%s> %s',
                     (self._address, self._port), msg.address, msg.params)
        return super().send(msg)

    def send_board(self, board, topic):
        mb = self.message_builder(topic)
        for tile in board.tiles:
            mb.add_arg(conf.LEMUR_UI_BOARDS[topic][tile.current])
        msg = mb.build()
        self.send(msg)
        return msg


class Server(Process):
    name = 'battleship_osc_server'
    daemon = True

    def __init__(self, server_address, queue, topic_mapping=conf.OSC_TOPICS):
        super().__init__()
        self.server_address = server_address
        # map all the topics to osc_addresses
        self.dispatcher = dispatcher.Dispatcher()
        for topic, osc_addresses in topic_mapping.items():
            osc_address = osc_addresses[0]
            self.dispatcher.map(osc_address, self._enqueue, osc_address, topic)
        self._queue = queue
        self._last_message = None

    def _enqueue(self, args, *msg):
        if msg != self._last_message:
            self._last_message = msg
            osc_addr, topic = args
            logger.debug('OSC recv <%s> on <%s> %s',
                         self.server_address, osc_addr, msg)
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
