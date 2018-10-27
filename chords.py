#!/usr/bin/python

import mido, sys, time

turn_off_map = {}

piano = mido.open_ioport('CASIO USB-MIDI:CASIO USB-MIDI MIDI 1')

midi = mido.MidiFile(sys.argv[1])
chords = []
for event in midi:
    if event.type != 'note_on': continue
    if event.velocity == 0: continue
    if event.time != 0 or not chords: chords.append([])
    chords[-1].append(event.note)

enabled = False
i = 0
def get_voicing(event):
    global i
    if enabled and event.note == max(chords[i]):
        result = chords[i]
        i = (i + 1) % len(chords)
        return result
    return []  # [event.note] if local control is off

while True:
    event = piano.receive()
    if event:
        if event.type == 'note_on':
            event.time = time.time()
            voicing = get_voicing(event)
            for note in voicing:
                if turn_off_map.get(note, None):
                    # workaround for the stuck note bug
                    piano.send(event.copy(note=note, velocity=0))
                turn_off_map[note] = event.note
                piano.send(event.copy(note=note))
        elif event.type == 'note_off':
            for note in turn_off_map:
                if turn_off_map[note] == event.note:
                    piano.send(event.copy(note=note))
                    turn_off_map[note] = None
        elif (event.type == 'control_change' and event.channel == 0
              and event.control == 67 and event.value == 127):
            enabled = not enabled
            i = 0
        else:
            piano.send(event)

"""
Current status:
* Notes occasionally get stuck on. Adding in a reset() whenever
  the turn_off_dict is empty will largely mitigate the symptoms,
  but not the problem.
* Rate limiting is not the solution. 0.1 second delay between
  commands and the sequence below still sticks a note every time.
* Appears to be a bug in the Casio reverb unit when the same note
  is turned on > 3 times in rapid succession.

sequence

on 58
on 64
on 68
on 72
on 56
on 58
on 64
on 68
off 72
on 52
on 58
on 61
on 64
off 56
off 68
on 48
on 52
on 54
on 58
on 60
on 56
on 60
on 64
on 67
off 58
off 54
off 52
off 48
off 61
off 56
off 60
off 64
off 67

reliably sticks 64

"""
