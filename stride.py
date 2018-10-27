#!/usr/bin/python

import mido, time

max_notes   = 3     # chords are considered complete after this many notes
max_latency = 0.03  # seconds to wait before a chord is considered complete

events = []
turn_off_map = {}

def chord_ready():
    return ((len(events) > 0 and time.time() - events[-1].time > max_latency)
            or len(events) >= max_notes)

def get_voicing(chord):
    if len(chord) == 0:  # 1 note
        # bass note alone is 1 octave down
        return [-12, 0]
    if len(chord) == 1:  # 2 notes
        if chord[0] in [3, 4]:
            # Thirds signify the corresponding major/minor triad (same root)
            return [0, 7, chord[0] + 12]
        if chord[0] in [8, 9]:
            # Sixths signify the cooresponding major/minor triad (6 inversion)
            return [0, chord[0], chord[0] + 7]
        if chord[0] in [10, 11]:
            # Sevenths specify the corresponding seventh chord
            return [0, chord[0], 16, 19]
    # Default: keep it the same
    return [0] + chord

piano = mido.open_ioport('CASIO USB-MIDI:CASIO USB-MIDI MIDI 1')

while True:
    event = piano.poll()
    if event:
        if event.type == 'note_on' and event.note < 60:
            event.time = time.time()
            events.append(event)
        elif event.type == 'note_off' and event.note < 60:
            for note in turn_off_map:
                if turn_off_map[note] == event.note:
                    piano.send(event.copy(note=note))
                    turn_off_map[note] = None
        else:
            piano.send(event)
    if chord_ready():
        velocity = int(sum([event.velocity for event in events]) / len(events))
        notes = [event.note for event in events]
        notes.sort()
        chord = [n - notes[0] for n in notes[1:]]
        print('root {}, chord {}'.format(notes[0], chord))
        voicing = [n + notes[0] for n in get_voicing(chord)]
        for note in voicing:
            turn_off_map[note] = notes[0]
            piano.send(events[-1].copy(note=note, velocity=velocity))
        events = []
