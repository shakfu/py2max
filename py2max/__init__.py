"""py2max: A pure Python library for offline generation of Max/MSP patcher files.

py2max provides a Python object model that mirrors Max's patch organization with
round-trip conversion capabilities. It enables programmatic creation of Max/MSP
patches (.maxpat) files.

Main Classes:
    Patcher: Core class for creating and managing Max patches
    Box: Represents individual Max objects (oscillators, effects, etc.)
    Patchline: Represents connections between objects
    InvalidConnectionError: Exception raised for invalid connections

Example:
    >>> from py2max import Patcher
    >>> p = Patcher('my-patch.maxpat')
    >>> osc = p.add_textbox('cycle~ 440')
    >>> gain = p.add_textbox('gain~')
    >>> dac = p.add_textbox('ezdac~')
    >>> p.add_line(osc, gain)
    >>> p.add_line(gain, dac)
    >>> p.save()
"""

from .core import Patcher, Box, Patchline, InvalidConnectionError
from .db import MaxRefDB

__all__ = ["Patcher", "Box", "Patchline", "InvalidConnectionError", "MaxRefDB"]
