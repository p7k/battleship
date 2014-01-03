import unittest
import time
from multiprocessing import Queue
from battleship import player, board


class TestServerClient(unittest.TestCase):
    server_address = ('0.0.0.0', 5005)

    @classmethod
    def setUpClass(cls):
        cls.mq = Queue()
        topic_mapping = dict(us=('/test/address/', '/test/address/'))
        cls.server = player.Server(cls.server_address, cls.mq, topic_mapping)
        cls.server.start()
        cls.client = player.Client('localhost', 5005, topic_mapping)
        time.sleep(.1)

    def test_send_receive_through_queue(self):
        # build msg
        msg_bldr = self.client.message_builder('us')
        msg_bldr.add_arg(46)
        msg_bldr.add_arg(2)
        sent_msg = msg_bldr.build()
        # send msg
        self.client.send(sent_msg)
        # get msg off the queue
        queued_msg = self.mq.get(timeout=1)
        # check msg
        self.assertEqual(queued_msg,
                         (self.server_address, 'us', tuple(sent_msg.params)))

    def test_send_receive_board_through_queue(self):
        sent_msg = self.client.send_board(board.Board(), 'us')
        queued_msg = self.mq.get(timeout=1)
        self.assertEqual(queued_msg,
                         (self.server_address, 'us', tuple(sent_msg.params)))

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()


class TestGame(unittest.TestCase):
    def setUp(self):
        self.game = player.Game()

    def test_game(self):
        self.game.start()
