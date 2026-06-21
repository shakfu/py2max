"""Named Max colors, color resolution, and box themes.

Max stores colors as ``[r, g, b, a]`` float lists in the 0..1 range. These
helpers let callers use friendly names (``"red"``), hex strings (``"#ff8800"``),
or raw float sequences interchangeably when styling boxes.
"""

from typing import Dict, List, Sequence, Union

# A color may be given as a name, a hex string, or an [r, g, b(, a)] sequence.
ColorLike = Union[str, Sequence[float]]

# Named colors as Max RGBA floats (0..1).
MAX_COLORS: Dict[str, List[float]] = {
    "black": [0.0, 0.0, 0.0, 1.0],
    "white": [1.0, 1.0, 1.0, 1.0],
    "red": [0.85, 0.0, 0.0, 1.0],
    "green": [0.0, 0.6, 0.0, 1.0],
    "blue": [0.0, 0.0, 1.0, 1.0],
    "yellow": [1.0, 0.9, 0.0, 1.0],
    "cyan": [0.0, 0.8, 0.9, 1.0],
    "magenta": [0.9, 0.0, 0.9, 1.0],
    "orange": [1.0, 0.6, 0.0, 1.0],
    "purple": [0.6, 0.2, 0.8, 1.0],
    "gray": [0.5, 0.5, 0.5, 1.0],
    "grey": [0.5, 0.5, 0.5, 1.0],
    "lightgray": [0.83, 0.83, 0.83, 1.0],
    "lightgrey": [0.83, 0.83, 0.83, 1.0],
    "darkgray": [0.27, 0.27, 0.27, 1.0],
    "darkgrey": [0.27, 0.27, 0.27, 1.0],
    "clear": [0.0, 0.0, 0.0, 0.0],
}


def _hex_to_rgba(hex_color: str) -> List[float]:
    """Convert ``#rrggbb`` or ``#rrggbbaa`` to a Max RGBA float list."""
    s = hex_color.lstrip("#")
    if len(s) == 6:
        s += "ff"
    if len(s) != 8:
        raise ValueError(f"invalid hex color {hex_color!r}")
    try:
        return [int(s[i : i + 2], 16) / 255.0 for i in (0, 2, 4, 6)]
    except ValueError as exc:
        raise ValueError(f"invalid hex color {hex_color!r}") from exc


def resolve_color(color: ColorLike) -> List[float]:
    """Resolve a color to a Max ``[r, g, b, a]`` float list.

    Accepts a named color (see ``MAX_COLORS``), a hex string (``"#rrggbb"`` or
    ``"#rrggbbaa"``), or an ``[r, g, b]`` / ``[r, g, b, a]`` sequence of floats.
    """
    if isinstance(color, str):
        key = color.strip().lower()
        if key in MAX_COLORS:
            return list(MAX_COLORS[key])
        if key.startswith("#"):
            return _hex_to_rgba(key)
        raise ValueError(f"unknown color name {color!r}")
    seq = [float(c) for c in color]
    if len(seq) == 3:
        seq.append(1.0)
    if len(seq) != 4:
        raise ValueError(f"color sequence must have 3 or 4 components, got {color!r}")
    return seq


# Box-color themes applied to every box by Patcher.apply_theme.
THEMES: Dict[str, Dict[str, ColorLike]] = {
    "light": {"bg": "lightgray", "text": "black", "border": "gray"},
    "dark": {
        "bg": [0.15, 0.15, 0.15, 1.0],
        "text": "white",
        "border": [0.4, 0.4, 0.4, 1.0],
    },
    "blue": {
        "bg": [0.85, 0.9, 1.0, 1.0],
        "text": [0.05, 0.1, 0.3, 1.0],
        "border": "blue",
    },
    "high-contrast": {"bg": "black", "text": "yellow", "border": "yellow"},
}
