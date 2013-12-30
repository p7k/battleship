"""Game settings.

Board, Ships, OSC, Player
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
OSC_ADDR_US = '/us/x'
OSC_ADDR_THEM = '/them/x'
OSC_ADDR_READY = '/ready/x'

# tuple of ip, port
PLAYER_1 = ('0.0.0.0', 5005)
PLAYER_2 = ('', 5005)
