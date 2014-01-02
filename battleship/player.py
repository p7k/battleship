import logging
from multiprocessing import Process
from pythonosc import dispatcher, osc_server, udp_client, osc_message_builder
from battleship import conf

logger = logging.getLogger(__name__)


def message_builder(topic):
    return osc_message_builder.OscMessageBuilder(conf.OSC_TOPICS[topic])


class Client(udp_client.UDPClient):
    def send(self, msg):
        """adds logging"""
        logger.debug('OSC send %s: %s', msg.address, msg.params)
        return super().send(msg)

    def send_board(self, board, topic):
        mb = message_builder(topic)
        for tile in board.tiles:
            mb.add_arg(conf.LEMUR_UI_BOARDS[topic][tile.current])
        msg = mb.build()
        self.send(msg)
        return msg


class Server(Process):
    name = 'battleship_osc_server'
    daemon = True

    def __init__(self, osc_server_address, queue):
        super().__init__()
        self._queue = queue
        self.server_address = osc_server_address
        # map all the topics to osc_addresses
        self.dispatcher = dispatcher.Dispatcher()
        for topic, osc_address in conf.OSC_TOPICS.items():
            self.dispatcher.map(osc_address, self._enqueue, topic)
        self._last_msg = None

    def _enqueue(self, args, *msg):
        if msg != self._last_msg:
            topic = args[0]
            self._queue.put((topic, msg))

    def run(self):
        logger.info('starting osc server')
        server = osc_server.ThreadingOSCUDPServer(self.server_address,
                                                  self.dispatcher)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        finally:
            server.server_close()
