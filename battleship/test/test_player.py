import unittest
import time
from multiprocessing import Queue
from pythonosc import osc_message_builder
from pythonosc import udp_client
from battleship import player, conf, board


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.queue = Queue()
        ip, port = '127.0.0.1', 5005
        self.player = player.Player((ip, port), self.queue)
        self.player.start()
        self.client = udp_client.UDPClient(ip, port)
        time.sleep(.1)

    def test_receive_through_queue(self):
        # build msg
        msg_bldr = osc_message_builder.OscMessageBuilder(conf.OSC_ADDR_US)
        msg_bldr.add_arg(46)
        msg_bldr.add_arg(2)
        sent_msg = msg_bldr.build()
        # send msg
        self.client.send(sent_msg)
        # get msg off the queue
        queued_msg = self.queue.get(timeout=1)
        # check msg
        self.assertEqual(queued_msg, ('us', tuple(sent_msg.params)))

    def tearDown(self):
        self.player.terminate()


class TestPlayerBoard(unittest.TestCase):
    def setUp(self):
        self.queue = Queue()
        self.player = player.Player(conf.PLAYER_1, self.queue)
        self.player.start()

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
        self.player.terminate()
