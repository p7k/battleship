import unittest
import time
from multiprocessing import Queue
from battleship import player, board


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
        sent_msg = self.client.send_board(board.Board(), 'us')
        queued_msg = self.queue.get(timeout=1)
        self.assertEqual(queued_msg,
                         (self.server_address, 'us', tuple(sent_msg.params)))

    def tearDown(self):
        self.server.terminate()


class TestGame(unittest.TestCase):
    def setUp(self):
        self.game = player.Game()

    def test_game(self):
        self.game.start()
