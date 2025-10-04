"""Utility functions for py2max.

This module provides helper functions for common Max/MSP operations
such as pitch-to-frequency conversion and other musical calculations.
"""

NOTE_TO_SEMITONE = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "E#": 5,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
    "B#": 0,
}


def pitch2freq(pitch, A4=440):
    """Convert a pitch name to a frequency in Hz.

    Converts standard pitch notation (e.g., "C4", "A#3") to frequency
    values using equal temperament tuning.

    Args:
        pitch: Pitch name in format like "C4", "A#3", "Bb2".
        A4: Reference frequency for A4 (default: 440 Hz).

    Returns:
        Frequency in Hz as a float.

    Example:
        >>> pitch2freq("C3")
        130.8127826502993
        >>> pitch2freq("A4")
        440.0

    Note:
        Based on: https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e
    """

    token = pitch.strip()
    if len(token) < 2:
        raise ValueError(f"Invalid pitch name: '{pitch}'")

    note = token[0].upper()
    idx = 1

    if idx < len(token) and token[idx] in ("#", "b", "♯", "♭"):
        accidental = token[idx]
        if accidental == "♯":
            accidental = "#"
        elif accidental == "♭":
            accidental = "b"
        note += accidental
        idx += 1

    octave_part = token[idx:]
    try:
        octave = int(octave_part)
    except ValueError as exc:
        raise ValueError(f"Invalid octave in pitch name: '{pitch}'") from exc

    if note not in NOTE_TO_SEMITONE:
        raise ValueError(f"Unsupported note name: '{pitch}'")

    semitone = NOTE_TO_SEMITONE[note]
    midi_number = semitone + (octave + 1) * 12
    distance_from_A4 = midi_number - 69
    return float(A4) * 2 ** (distance_from_A4 / 12)
