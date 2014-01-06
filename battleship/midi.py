"""Simple MIDI controller.

All triggers are NoteOn messages.
"""
import rtmidi2
from battleship import conf

OUT = rtmidi2.MidiOut()
OUT.open_port(OUT.ports_matching(conf.MIDI_DRIVER_NAME)[0])


def send_noteon(ch, pitch, velocity=127):
    OUT.send_noteon(conf.MIDI_CHANNELS[ch], pitch, 127)


def start(pitch):
    send_noteon('start', pitch)


def stop(pitch):
    send_noteon('stop', pitch)


def crush(pitch):
    send_noteon('crush', pitch)
