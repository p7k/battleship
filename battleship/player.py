import logging
from multiprocessing import Process
from pythonosc import dispatcher
from pythonosc import osc_server
from battleship import conf

logger = logging.getLogger(__name__)


class Player(Process):
    name = 'Player'
    daemon = True

    def __init__(self, osc_server_address, queue):
        super().__init__()
        self._server_address = osc_server_address
        self._queue = queue
        self._dispatcher = dispatcher.Dispatcher()
        self._dispatcher.map(conf.OSC_US_ADDR, self._enqueue)
        self._last_msg = None

    def _enqueue(self, *msg):
        if msg != self._last_msg:
            self._queue.put((1, msg))

    def run(self):
        logger.info('starting osc server')
        server = osc_server.ThreadingOSCUDPServer(self._server_address,
                                                  self._dispatcher)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        finally:
            server.server_close()
