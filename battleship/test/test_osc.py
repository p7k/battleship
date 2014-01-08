import unittest
import multiprocessing
import time
from battleship import board, osc


class TestServerClient(unittest.TestCase):
    server_address = ('0.0.0.0', 5005)

    @classmethod
    def setUpClass(cls):
        cls.mq = multiprocessing.Queue()
        topic_mapping = dict(us=('/test/address/', '/test/address/'))
        cls.server = osc.Server(cls.server_address, cls.mq, topic_mapping)
        cls.server.start()
        cls.client = osc.Client('localhost', 5005, topic_mapping)
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
