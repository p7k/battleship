import unittest
from battleship import game


class TestGameManager(unittest.TestCase):
    def setUp(self):
        self.game_manager = game.GameManager()

    def test_game(self):
        self.game_manager.start()
