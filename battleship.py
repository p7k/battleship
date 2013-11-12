import rtmidi2 as midi
import gevent


midi_out = midi.MidiOut()
midi_out.ports
index = midi_out.ports_matching('Daemon Output 0')[0]
print index
midi_out.open_port(index)


def play_note(channel=1, pitch=60, velocity=127, duration=1):
    midi_out.send_noteon(channel, pitch, velocity)
    gevent.sleep(duration)
    midi_out.send_noteoff(channel, pitch)


def snake(ch=1):
    for pitch in range(25):
        play_note(channel=ch, pitch=pitch, duration=.05)


# map(snake, (2, 3, 1))


gevent.joinall((gevent.spawn(snake),))

# channel mappings to cell states


CH_EMPTY = CH_PLACED = 1
CH_MISS = 2
CH_HIT = 3


def place(i, velocity=127):
    midi_out.send_noteon(CH_PLACED, i, velocity)


def clear(i):
    midi_out.send_noteoff(CH_EMPTY, i)


def miss(i):
    midi_out.send_noteoff(CH_MISS, i)


def hit(i):
    midi_out.send_noteoff(CH_HIT, i)


miss(24)
clear(24)
place(24)
hit(24)

# Locking a state

# midi_in = midi.MidiIn()
# port_index_in = midi_in.ports_matching('Daemon Input 0')


# def lock_hit(msg, timestamp):
#     print msg
#     if msg[0] == 144 and msg[2] > 0:
#         print 'lock'
#         hit(msg[1])
# 
# midi_in.callback = lock_hit
# midi_in.open_port(port_index_in[0])

# while True:
#     pass
