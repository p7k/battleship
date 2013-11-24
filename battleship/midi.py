"""Simple MIDI controller.

All triggers are NoteOn messages.

Channel 1, 2:  loop start
Channel 3, 4:  loop stop
Channel 5, 6:  loop crush
"""
import rtmidi2 as midi

DRIVER_NAME = b'IAC Driver Battleship'

OUT = midi.MidiOut()
OUT.open_port(OUT.ports_matching(DRIVER_NAME)[0])


def start(pitch):
    OUT.send_noteon(0, pitch, 127)


def stop(pitch):
    OUT.send_noteon(2, pitch, 127)


def crush(pitch):
    OUT.send_noteon(4, pitch, 127)
