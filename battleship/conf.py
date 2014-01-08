"""Game settings.

Board, Ships, MIDI, OSC, LEMUR_UI, Player
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

# midi
MIDI_DRIVER_NAME = b'IAC Driver Battleship'
MIDI_CHANNELS = {'start': 0, 'stop': 2, 'crush': 4}
MIDI_PITCH_RANGE = range(36, 58)

# osc addresses
OSC_TOPICS = {'us': ('/us/x', '/us/draw'),
              'them': ('/them/x', '/them/draw'),
              'ready': ('/ready/x', '/ready/x'),
              'ready_light': ('/ready/light', '/ready/light'),
              'turn': ('/turn/value', '/turn/value'),
              'turn_light': ('/turn/light', '/turn/light')}

# lemur ui
LEMUR_UI_BOARDS = {'us':   {'sea': 0, 'deck': 1, 'miss': 2, 'hit': 3},
                   'them': {'sea': 0, 'deck': 0, 'miss': 2, 'hit': 3}}

# list of tuples of (ip, port)
PLAYERS = [{'client_address': ('alice.local', 8000),
            'server_address': ('0.0.0.0', 5005)},
           {'client_address': ('thrace.local', 8000),
            'server_address': ('0.0.0.0', 5006)}]

# game timeout (seconds)
GAME_TIMEOUT = 60*10

# time ignore message
IGNORE_TIME_GAME_OVER = 10
