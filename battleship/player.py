import logging
import time
from multiprocessing import Process
from pythonosc import dispatcher, osc_server, udp_client, osc_message_builder
from battleship import conf

logger = logging.getLogger(__name__)
SERVER_BIND = '0.0.0.0'


class Player:
    def __init__(self, player_id, game_queue, host, port_client, port_server):
        self.server = Server((SERVER_BIND, port_server), game_queue, player_id)
        self.server.start()
        time.sleep(.1)
        self.client = Client(host, port_client, )

    def terminate_server(self):
        self.server.terminate()


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
        self._last_msg = None

    def _enqueue(self, args, *msg):
        if msg != self._last_msg:
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
