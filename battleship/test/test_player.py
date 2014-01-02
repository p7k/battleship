import unittest
import time
from multiprocessing import Queue
from battleship import player, conf, board


class TestServerClient(unittest.TestCase):
    def setUp(self):
        self.queue = Queue()
        self.player = 1
        self.server_address = ('0.0.0.0', 5005)
        self.server = player.Server(self.server_address, self.queue)
        self.server.start()
        self.client = player.Client('localhost', 5005)
        time.sleep(.1)

    def test_send_receive_through_queue(self):
        # build msg
        msg_bldr = player.message_builder('us')
        msg_bldr.add_arg(46)
        msg_bldr.add_arg(2)
        sent_msg = msg_bldr.build()
        # send msg
        self.client.send(sent_msg)
        # get msg off the queue
        queued_msg = self.queue.get(timeout=1)
        # check msg
        self.assertEqual(queued_msg,
                         (self.server_address, 'us', tuple(sent_msg.params)))

    def test_send_receive_board_through_queue(self):
        test_board = board.Board(conf.BOARD_SIZE, conf.SHIP_SPEC)
        sent_msg = self.client.send_board(test_board, 'us')
        queued_msg = self.queue.get(timeout=1)
        self.assertEqual(queued_msg,
                         (self.server_address, 'us', tuple(sent_msg.params)))

    def tearDown(self):
        self.server.terminate()


class TestPlayerBoard(unittest.TestCase):
    def setUp(self):
        self.queue = Queue()
        self.server = player.Server(ip, port, self.queue)
        self.server.start()

    def test_board(self):
        self.board = board.Board(conf.BOARD_SIZE, conf.SHIP_SPEC)
        while True:
            try:
                p, msg = self.queue.get()
                for i, on in enumerate(msg):
                    if on:
                        self.board.add(i)
                print(self.board)
                print(self.board.current)
            except KeyboardInterrupt:
                break

    def tearDown(self):
        self.server.terminate()
