"""py2max.utils

A module for simple helper functions and classes for py2max

"""

def pitch2freq(pitch, A4=440):
    """
    Convert a pitch to a frequency

    >>> pitch2freq("C3")
    130.8127826502993

    from: https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e#file-note_to_freq-py
    """
    notes = ['A', 'Bb', 'B', 'C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab']
    note = notes.index(pitch[:-1])
    octave = int(pitch[-1])
    distance_from_A4 = note + 12 * (octave - (4 if note < 3 else 5))
    return A4 * 2 ** (distance_from_A4/12)
