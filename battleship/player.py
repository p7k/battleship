import logging
import time
import fysom
from multiprocessing import Process
from pythonosc import dispatcher, osc_server, udp_client, osc_message_builder
from battleship import conf

logger = logging.getLogger(__name__)


class Player(fysom.Fysom):
    def __init__(self, game_queue, server_address, client_address):
        self.server = Server(server_address, game_queue)
        self.server.start()
        time.sleep(.2)
        self.client = Client(*client_address)
        super().__init__(
            dict(initial='setup', final='play',
                 events=(dict(name='prompt', src='setup', dst='confirmation'),
                         dict(name='confirm', src='confirmation', dst='ready'),
                         dict(name='deny', src='ready', dst='confirmation'),
                         dict(name='play', src='ready', dst='play'))))

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

    def confirmation_button(self, on=True):
        mb = self.message_builder('ready_light')
        mb.add_arg(0 if on else -2)
        self.send(mb.build())

    def confirmation_value(self, on=True):
        mb = self.message_builder('ready')
        mb.add_arg(1 if on else 0)
        self.send(mb.build())

    def turn_led(self, on=True):
        mb = self.message_builder('turn_light')
        mb.add_arg(0 if on else -2)
        self.send(mb.build())

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
