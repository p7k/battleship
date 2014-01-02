"""Game settings.

Board, Ships, OSC, LEMUR_UI, Player
"""
import logging

# logging
logging.basicConfig(
    format='%(asctime)-24s%(levelname)-10s%(name)-25s%(message)s',
    level=logging.DEBUG)

# board will be n x n
BOARD_SIZE = 5

# list of tuples of (size, qty)
SHIP_SPEC = [(1, 2),
             (2, 1),
             (3, 1),
             (4, 1)]

# osc addresses
OSC_TOPICS = {'us': '/us/x',
              'them': '/them/x',
              'ready': '/ready/x'}

# lemur ui
LEMUR_UI_BOARDS = {'us':   {'sea': 0, 'deck': 1, 'miss': 2, 'hit': 3},
                   'them': {'sea': 0, 'deck': 0, 'miss': 2, 'hit': 3}}

# list of tuples of (ip, port)
PLAYERS = [{'client': ('alice.local', 8000),
            'server': ('0.0.0.0', 5005)},
           {'client': ('thetis.local', 8000),
            'server': ('0.0.0.0', 5006)}]
