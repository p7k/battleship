"""Game settings.

Board, Ships, OSC, LEMUR_UI, Player
"""
import logging

# logging
logging.basicConfig(
    format='%(asctime)-24s%(levelname)-10s%(name)-25s%(message)s',
    level=logging.DEBUG)

# board will be n^2
BOARD_SIZE = 5

# list of tuples of size, qty
SHIP_SPEC = [(1, 2), (2, 1), (3, 1), (4, 1)]

# osc addresses
OSC_TOPICS = dict(us='/us/x', them='/them/x', ready='/ready/x')

# lemur ui
LEMUR_UI_BOARDS = dict(us=dict(sea=0, deck=1, miss=2, hit=3),
                       them=dict(sea=0, deck=0, miss=2, hit=3))

# tuple of ip, port
PLAYER_1 = ('0.0.0.0', 5005)
PLAYER_2 = ('', 5005)
