"""Utility functions for py2max.

This module provides helper functions for common Max/MSP operations
such as pitch-to-frequency conversion and other musical calculations.
"""


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
    notes = ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab"]
    note = notes.index(pitch[:-1])
    octave = int(pitch[-1])
    distance_from_A4 = note + 12 * (octave - (4 if note < 3 else 5))
    return A4 * 2 ** (distance_from_A4 / 12)
