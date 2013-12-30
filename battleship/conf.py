"""Game settings.

Board, Ships, OSC, Player
"""

# board will be n^2
BOARD_SIZE = 5

# list of tuples of size, qty
SHIP_SPEC = [(1, 2), (2, 1), (3, 1), (4, 1)]

# osc addresses
OSC_US_ADDR = '/us2/x'

# tuple of ip, port
PLAYER_1 = ('0.0.0.0', 5005)
PLAYER_2 = ('', 5005)
