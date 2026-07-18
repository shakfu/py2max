"""SVG export functionality for py2max patches.

This module exports Max/MSP patch layouts to SVG for offline visual validation
without requiring Max. It aims for a faithful-ish preview rather than a bare
schematic:

    - Honors per-box colors set via ``Box.set_color`` / ``apply_theme``
      (``bgcolor`` / ``bordercolor`` / ``textcolor``).
    - Draws recognizable affordances for common UI objects (message, toggle,
      button, number boxes, dial, slider) instead of a uniform grey rectangle.
    - Resolves inlet/outlet counts from the box's own ``numinlets`` /
      ``numoutlets`` (what actually gets written to the ``.maxpat``), so ports
      render correctly without a maxref lookup and patchline endpoints line up
      with the ports they connect to.
    - Colors ports and cables by signal vs message/control type.

Example:
    >>> from py2max import Patcher
    >>> from py2max.export import export_svg
    >>> p = Patcher('my-patch.maxpat')
    >>> osc = p.add_textbox('cycle~ 440')
    >>> dac = p.add_textbox('ezdac~')
    >>> p.add_line(osc, dac)
    >>> export_svg(p, '/tmp/my-patch.svg')
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from ..core import Patcher
    from ..core.abstract import AbstractBox, AbstractPatchline


# SVG styling constants -- approximate Max's default light theme.
BG_COLOR = "#cfcfcf"  # patcher background
BOX_FILL = "#e2e2e2"  # default object box
BOX_STROKE = "#8c8c8c"
BOX_STROKE_WIDTH = 1
COMMENT_FILL = "#ffffd0"
MESSAGE_FILL = "#dcdcdc"  # message box
SUBPATCHER_FILL = "#d3dcec"  # subpatchers get a blue tint
UI_FILL = "#f4f4f4"  # UI widgets (toggle/button/dial/slider/number)
UI_ACCENT = "#3a6ea5"  # UI indicator (dial pointer, slider thumb, ...)
TEXT_COLOR = "#1a1a1a"
TEXT_FONT_FAMILY = "Helvetica, Arial, sans-serif"
TEXT_FONT_SIZE = 12
# Connections: signal cables are drawn thicker and in a distinct color.
LINE_COLOR = "#5a5a5a"  # message/control cable
LINE_WIDTH = 1.2
SIGNAL_LINE_COLOR = "#b58900"  # signal cable
SIGNAL_LINE_WIDTH = 2.4
# Ports, colored by signal vs message/control.
SIGNAL_PORT_COLOR = "#2e8b57"  # signal inlets/outlets
MESSAGE_PORT_COLOR = "#1f1f1f"  # control/message inlets/outlets
PORT_RADIUS = 2.5
PADDING = 20

# UI objects whose glyph replaces a text label.
_ICON_ONLY = {"toggle", "button", "bng", "dial", "slider"}


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _escape_text(text: str) -> str:
    """Escape text for SVG."""
    return html.escape(str(text))


def _kwd(box: AbstractBox, key: str) -> object:
    """Read a value out of the box's stored keyword attributes."""
    kw = getattr(box, "_kwds", None)
    if isinstance(kw, dict):
        return kw.get(key)
    return None


def _rgba_to_css(seq: object) -> Optional[str]:
    """Convert a Max ``[r, g, b, a]`` float list (0..1) to a CSS color.

    Returns ``None`` when ``seq`` is not a usable color sequence.
    """
    if not isinstance(seq, (list, tuple)) or len(seq) < 3:
        return None
    try:
        r, g, b = (int(round(float(seq[i]) * 255)) for i in range(3))
        a = float(seq[3]) if len(seq) > 3 else 1.0
    except (TypeError, ValueError):
        return None
    r, g, b = (max(0, min(255, c)) for c in (r, g, b))
    if a >= 1.0:
        return f"rgb({r},{g},{b})"
    return f"rgba({r},{g},{b},{a:.3f})"


def _rect_of(box: AbstractBox) -> Optional[Tuple[float, float, float, float]]:
    """Return ``(x, y, w, h)`` for a box, or ``None`` if it has no rect."""
    rect = getattr(box, "patching_rect", None)
    if not rect:
        return None
    if hasattr(rect, "x"):
        return (float(rect.x), float(rect.y), float(rect.w), float(rect.h))
    if isinstance(rect, (list, tuple)) and len(rect) >= 4:
        return (float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
    return None


def _is_subpatcher(box: AbstractBox) -> bool:
    """True if the box embeds a subpatcher (``p``, ``bpatcher``, ``poly~`` ...)."""
    if getattr(box, "subpatcher", None) is not None:
        return True
    text = str(getattr(box, "text", "") or "")
    return text == "p" or text.startswith(
        ("p ", "bpatcher", "poly~", "gen~", "gen ", "rnbo~")
    )


# --------------------------------------------------------------------------- #
# Colors
# --------------------------------------------------------------------------- #
def _default_fill(box: AbstractBox) -> str:
    maxclass = getattr(box, "maxclass", "newobj")
    if maxclass == "comment":
        return COMMENT_FILL
    if maxclass == "message":
        return MESSAGE_FILL
    if maxclass in ("toggle", "button", "bng", "dial", "slider", "number", "flonum"):
        return UI_FILL
    if _is_subpatcher(box):
        return SUBPATCHER_FILL
    return BOX_FILL


def _box_colors(box: AbstractBox) -> Tuple[str, str, str]:
    """Return ``(fill, stroke, text_color)`` honoring user-set box colors."""
    fill = _rgba_to_css(_kwd(box, "bgcolor")) or _default_fill(box)
    stroke = (
        _rgba_to_css(_kwd(box, "bordercolor"))
        or _rgba_to_css(_kwd(box, "color"))
        or BOX_STROKE
    )
    text_color = (
        _rgba_to_css(_kwd(box, "textcolor"))
        or _rgba_to_css(_kwd(box, "color"))
        or TEXT_COLOR
    )
    return fill, stroke, text_color


# --------------------------------------------------------------------------- #
# Ports (counts come from the box's own numinlets/numoutlets)
# --------------------------------------------------------------------------- #
def _outlet_types(box: AbstractBox) -> List[str]:
    ot = getattr(box, "outlettype", None)
    if isinstance(ot, (list, tuple)) and ot:
        return [str(t) for t in ot]
    if hasattr(box, "get_outlet_types"):
        try:
            return [str(t) for t in (box.get_outlet_types() or [])]
        except Exception:
            return []
    return []


def _inlet_types(box: AbstractBox) -> List[str]:
    if hasattr(box, "get_inlet_types"):
        try:
            return [str(t) for t in (box.get_inlet_types() or [])]
        except Exception:
            return []
    return []


def _port_color(types: List[str], idx: int) -> str:
    if idx < len(types) and types[idx] == "signal":
        return SIGNAL_PORT_COLOR
    return MESSAGE_PORT_COLOR


def _inlet_count(box: AbstractBox) -> int:
    """Number of inlets to draw.

    The box's own ``numinlets`` is authoritative -- it is what gets written to
    the ``.maxpat`` and therefore matches Max's real port layout, and it needs
    no maxref lookup. Fall back to maxref, then to a private cache, only when
    the box does not declare it.
    """
    n = getattr(box, "numinlets", None)
    if n is not None:
        return int(n)
    if hasattr(box, "get_inlet_count"):
        try:
            return int(box.get_inlet_count() or 0)
        except Exception:
            pass
    return int(getattr(box, "_inlet_count", 0) or 0)


def _outlet_count(box: AbstractBox) -> int:
    """Number of outlets to draw (see :func:`_inlet_count`)."""
    n = getattr(box, "numoutlets", None)
    if n is not None:
        return int(n)
    if hasattr(box, "get_outlet_count"):
        try:
            return int(box.get_outlet_count() or 0)
        except Exception:
            pass
    return int(getattr(box, "_outlet_count", 0) or 0)


def _render_ports(box: AbstractBox, x: float, y: float, w: float, h: float) -> str:
    parts = []
    ic = _inlet_count(box)
    if ic > 0:
        itypes = _inlet_types(box)
        spacing = w / (ic + 1)
        for i in range(ic):
            parts.append(
                f'<circle cx="{x + spacing * (i + 1)}" cy="{y}" r="{PORT_RADIUS}" '
                f'fill="{_port_color(itypes, i)}" stroke="{BOX_STROKE}" '
                f'stroke-width="0.5" />'
            )
    oc = _outlet_count(box)
    if oc > 0:
        otypes = _outlet_types(box)
        spacing = w / (oc + 1)
        for i in range(oc):
            parts.append(
                f'<circle cx="{x + spacing * (i + 1)}" cy="{y + h}" r="{PORT_RADIUS}" '
                f'fill="{_port_color(otypes, i)}" stroke="{BOX_STROKE}" '
                f'stroke-width="0.5" />'
            )
    return "\n".join(parts)


def _get_port_position(
    box: AbstractBox, port_index: int, is_outlet: bool
) -> Tuple[float, float]:
    """x,y of an inlet/outlet, using the same counts as :func:`_render_ports`."""
    r = _rect_of(box)
    if r is None:
        return (0.0, 0.0)
    x, y, w, h = r
    count = _outlet_count(box) if is_outlet else _inlet_count(box)
    count = max(count, 1)  # avoid div-by-zero; a connected port implies >=1
    spacing = w / (count + 1)
    port_x = x + spacing * (port_index + 1)
    port_y = y + h if is_outlet else y
    return (port_x, port_y)


# --------------------------------------------------------------------------- #
# Box shapes
# --------------------------------------------------------------------------- #
def _rect(x: float, y: float, w: float, h: float, fill: str, stroke: str) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{BOX_STROKE_WIDTH}" rx="2" />'
    )


def _message_shape(
    x: float, y: float, w: float, h: float, fill: str, stroke: str
) -> str:
    """A message box: rectangle with a small flag notch on the right edge."""
    flag = min(h * 0.4, 8.0)
    right = x + w
    path = (
        f"M {x} {y} L {right - flag} {y} L {right} {y + h / 2} "
        f"L {right - flag} {y + h} L {x} {y + h} Z"
    )
    return (
        f'<path d="{path}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{BOX_STROKE_WIDTH}" />'
    )


def _toggle_glyph(x: float, y: float, w: float, h: float, stroke: str) -> str:
    ins = min(w, h) * 0.22
    return (
        f'<line x1="{x + ins}" y1="{y + ins}" x2="{x + w - ins}" y2="{y + h - ins}" '
        f'stroke="{stroke}" stroke-width="1.5" />'
        f'<line x1="{x + w - ins}" y1="{y + ins}" x2="{x + ins}" y2="{y + h - ins}" '
        f'stroke="{stroke}" stroke-width="1.5" />'
    )


def _button_glyph(x: float, y: float, w: float, h: float, stroke: str) -> str:
    r = min(w, h) / 2 - min(w, h) * 0.18
    return (
        f'<circle cx="{x + w / 2}" cy="{y + h / 2}" r="{r}" fill="none" '
        f'stroke="{stroke}" stroke-width="1.2" />'
    )


def _number_glyph(x: float, y: float, w: float, h: float, stroke: str) -> str:
    """The little right-pointing triangle marker on a number box's left edge."""
    cy = y + h / 2
    return (
        f'<polygon points="{x + 3},{cy - 3} {x + 3},{cy + 3} {x + 7},{cy}" '
        f'fill="{stroke}" />'
    )


def _dial_glyph(x: float, y: float, w: float, h: float, stroke: str) -> str:
    cx, cy = x + w / 2, y + h / 2
    r = min(w, h) / 2 - 2
    # pointer toward the lower-left (a dial's minimum position)
    px = cx - r * 0.7
    py = cy + r * 0.7
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{stroke}" '
        f'stroke-width="1.2" />'
        f'<line x1="{cx}" y1="{cy}" x2="{px}" y2="{py}" stroke="{UI_ACCENT}" '
        f'stroke-width="1.5" />'
    )


def _slider_glyph(x: float, y: float, w: float, h: float, stroke: str) -> str:
    """A thumb bar; horizontal if wider than tall, else vertical."""
    if w >= h:
        tx = x + w * 0.3
        return (
            f'<line x1="{tx}" y1="{y + 2}" x2="{tx}" y2="{y + h - 2}" '
            f'stroke="{UI_ACCENT}" stroke-width="2.5" />'
        )
    ty = y + h * 0.7  # low value sits near the bottom
    return (
        f'<line x1="{x + 2}" y1="{ty}" x2="{x + w - 2}" y2="{ty}" '
        f'stroke="{UI_ACCENT}" stroke-width="2.5" />'
    )


def _render_shape(
    box: AbstractBox,
    maxclass: str,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    stroke: str,
) -> str:
    if maxclass == "message":
        return _message_shape(x, y, w, h, fill, stroke)
    base = _rect(x, y, w, h, fill, stroke)
    if maxclass == "toggle":
        return base + "\n" + _toggle_glyph(x, y, w, h, stroke)
    if maxclass in ("button", "bng"):
        return base + "\n" + _button_glyph(x, y, w, h, stroke)
    if maxclass in ("number", "flonum", "number~"):
        return base + "\n" + _number_glyph(x, y, w, h, stroke)
    if maxclass == "dial":
        return base + "\n" + _dial_glyph(x, y, w, h, stroke)
    if maxclass == "slider":
        return base + "\n" + _slider_glyph(x, y, w, h, stroke)
    return base


def _get_box_text(box: AbstractBox) -> str:
    text = getattr(box, "text", None)
    if text:
        return str(text)
    return getattr(box, "maxclass", "newobj")


def _text_svg(
    x: float, y: float, h: float, text: str, color: str, x_offset: float = 5.0
) -> str:
    return (
        f'<text x="{x + x_offset}" y="{y + h / 2 + TEXT_FONT_SIZE / 3}" '
        f'font-family="{TEXT_FONT_FAMILY}" font-size="{TEXT_FONT_SIZE}" '
        f'fill="{color}">{_escape_text(text)}</text>'
    )


def _render_box(box: AbstractBox, show_ports: bool = True) -> str:
    """Render a single box (shape, label, and ports) to SVG."""
    r = _rect_of(box)
    if r is None:
        return ""
    x, y, w, h = r
    maxclass = getattr(box, "maxclass", "newobj")
    fill, stroke, text_color = _box_colors(box)

    parts = [_render_shape(box, maxclass, x, y, w, h, fill, stroke)]

    # Text label -- skipped for icon-only widgets whose glyph is the content.
    if maxclass not in _ICON_ONLY:
        text = _get_box_text(box)
        if text:
            x_offset = 10.0 if maxclass in ("number", "flonum", "number~") else 5.0
            parts.append(_text_svg(x, y, h, text, text_color, x_offset))

    if show_ports:
        ports = _render_ports(box, x, y, w, h)
        if ports:
            parts.append(ports)

    return "\n".join(p for p in parts if p)


# --------------------------------------------------------------------------- #
# Patchlines
# --------------------------------------------------------------------------- #
def _render_patchline(line: AbstractPatchline, patcher: Patcher) -> str:
    src_id = getattr(line, "src", None)
    dst_id = getattr(line, "dst", None)
    if not src_id or not dst_id:
        return ""

    src_box = patcher._objects.get(src_id)
    dst_box = patcher._objects.get(dst_id)
    if not src_box or not dst_box:
        return ""

    source = getattr(line, "source", [src_id, 0])
    destination = getattr(line, "destination", [dst_id, 0])
    src_port = int(source[1]) if len(source) > 1 else 0
    dst_port = int(destination[1]) if len(destination) > 1 else 0

    x1, y1 = _get_port_position(src_box, src_port, is_outlet=True)
    x2, y2 = _get_port_position(dst_box, dst_port, is_outlet=False)

    # Signal cables (from a signal outlet) are drawn thicker and distinct.
    out_types = _outlet_types(src_box)
    is_signal = src_port < len(out_types) and out_types[src_port] == "signal"
    color = SIGNAL_LINE_COLOR if is_signal else LINE_COLOR
    width = SIGNAL_LINE_WIDTH if is_signal else LINE_WIDTH

    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" />'
    )


def _calculate_viewbox(patcher: Patcher) -> Tuple[float, float, float, float]:
    """Calculate SVG viewBox to fit all objects with padding."""
    boxes = patcher._boxes
    if not boxes:
        return (0.0, 0.0, 800.0, 600.0)

    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for box in boxes:
        r = _rect_of(box)
        if r is None:
            continue
        x, y, w, h = r
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x + w)
        max_y = max(max_y, y + h)

    if min_x == float("inf"):
        return (0.0, 0.0, 800.0, 600.0)

    min_x -= PADDING
    min_y -= PADDING
    max_x += PADDING
    max_y += PADDING
    return (min_x, min_y, max_x - min_x, max_y - min_y)


def _build_svg(
    patcher: Patcher, show_ports: bool = True, title: Optional[str] = None
) -> str:
    """Build the full SVG document for a patcher as a string."""
    vx, vy, vw, vh = _calculate_viewbox(patcher)

    parts: List[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vx} {vy} {vw} {vh}" width="{vw}" height="{vh}">',
        "",
        "<defs>",
        "  <style>",
        "    text { user-select: none; }",
        "  </style>",
        "</defs>",
        "",
        f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="{BG_COLOR}" />',
        "",
    ]

    if title:
        parts.append(
            f'<text x="{vx + vw / 2}" y="{vy + 20}" '
            f'font-family="{TEXT_FONT_FAMILY}" font-size="16" font-weight="bold" '
            f'fill="{TEXT_COLOR}" text-anchor="middle">{_escape_text(title)}</text>'
        )
        parts.append("")

    parts.append("<!-- Patchlines -->")
    for line in patcher._lines:
        line_svg = _render_patchline(line, patcher)
        if line_svg:
            parts.append(line_svg)
    parts.append("")

    parts.append("<!-- Boxes -->")
    for box in patcher._boxes:
        box_svg = _render_box(box, show_ports=show_ports)
        if box_svg:
            parts.append(box_svg)
    parts.append("")

    parts.append("</svg>")
    return "\n".join(parts)


def export_svg(
    patcher: Patcher,
    output_path: Union[str, Path],
    show_ports: bool = True,
    title: Optional[str] = None,
) -> None:
    """Export a patcher to SVG format.

    Args:
        patcher: The Patcher object to export.
        output_path: Output file path for the SVG.
        show_ports: Whether to show inlet/outlet ports on boxes.
        title: Optional title to display at top of SVG.

    Example:
        >>> p = Patcher('test.maxpat')
        >>> osc = p.add_textbox('cycle~ 440')
        >>> dac = p.add_textbox('ezdac~')
        >>> p.add_line(osc, dac)
        >>> export_svg(p, '/tmp/test.svg')
    """
    Path(output_path).write_text(
        _build_svg(patcher, show_ports=show_ports, title=title), encoding="utf-8"
    )


def export_svg_string(
    patcher: Patcher,
    show_ports: bool = True,
    title: Optional[str] = None,
) -> str:
    """Export a patcher to SVG format as a string.

    Args:
        patcher: The Patcher object to export.
        show_ports: Whether to show inlet/outlet ports on boxes.
        title: Optional title to display at top of SVG.

    Returns:
        SVG content as a string.

    Example:
        >>> p = Patcher('test.maxpat')
        >>> svg_str = export_svg_string(p)
    """
    return _build_svg(patcher, show_ports=show_ports, title=title)


__all__ = ["export_svg", "export_svg_string"]
