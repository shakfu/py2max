"""SVG export functionality for py2max patches.

This module provides functionality to export Max/MSP patch layouts to SVG format,
enabling offline visual validation without requiring Max.

Features:
    - Renders boxes with correct positioning and sizing
    - Draws patchlines with connection points
    - Supports different box types (comments, messages, objects)
    - Generates clean, scalable SVG output

Example:
    >>> from py2max import Patcher
    >>> from py2max.svg import export_svg
    >>> p = Patcher('my-patch.maxpat')
    >>> osc = p.add_textbox('cycle~ 440')
    >>> dac = p.add_textbox('ezdac~')
    >>> p.add_line(osc, dac)
    >>> export_svg(p, '/tmp/my-patch.svg')
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

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


def _outlet_types(box: AbstractBox) -> list[str]:
    """Outlet type strings for a box (``"signal"`` marks a signal outlet)."""
    ot = getattr(box, "outlettype", None)
    if isinstance(ot, (list, tuple)) and ot:
        return [str(t) for t in ot]
    if hasattr(box, "get_outlet_types"):
        try:
            return [str(t) for t in (box.get_outlet_types() or [])]
        except Exception:
            return []
    return []


def _inlet_types(box: AbstractBox) -> list[str]:
    """Inlet type strings for a box (``"signal"`` marks a signal inlet)."""
    if hasattr(box, "get_inlet_types"):
        try:
            return [str(t) for t in (box.get_inlet_types() or [])]
        except Exception:
            return []
    return []


def _port_color(types: list[str], idx: int) -> str:
    """Color a port green if it is a signal port, dark otherwise."""
    if idx < len(types) and types[idx] == "signal":
        return SIGNAL_PORT_COLOR
    return MESSAGE_PORT_COLOR


def _is_subpatcher(box: AbstractBox) -> bool:
    """True if the box embeds a subpatcher (``p``, ``bpatcher``, ``poly~`` ...)."""
    if getattr(box, "subpatcher", None) is not None:
        return True
    text = str(getattr(box, "text", "") or "")
    return text == "p" or text.startswith(
        ("p ", "bpatcher", "poly~", "gen~", "gen ", "rnbo~")
    )


def _escape_text(text: str) -> str:
    """Escape text for SVG."""
    return html.escape(str(text))


def _get_box_fill(box: AbstractBox) -> str:
    """Determine fill color based on box type."""
    maxclass = getattr(box, "maxclass", "newobj")
    if maxclass == "comment":
        return COMMENT_FILL
    elif maxclass == "message":
        return MESSAGE_FILL
    elif _is_subpatcher(box):
        return SUBPATCHER_FILL
    return BOX_FILL


def _get_box_text(box: AbstractBox) -> str:
    """Extract display text from a box."""
    text = getattr(box, "text", None)
    if text:
        return str(text)

    maxclass = getattr(box, "maxclass", "newobj")
    if maxclass == "comment":
        return getattr(box, "text", "")

    # For other object types, use maxclass name
    return maxclass


def _render_box(box: AbstractBox, show_ports: bool = True) -> str:
    """Render a single box to SVG elements."""
    rect = getattr(box, "patching_rect", None)
    if not rect:
        return ""

    # Handle both Rect objects and list/tuple representations
    if hasattr(rect, "x"):
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
    elif isinstance(rect, (list, tuple)) and len(rect) >= 4:
        x, y, w, h = rect[0], rect[1], rect[2], rect[3]
    else:
        return ""
    fill = _get_box_fill(box)
    text = _get_box_text(box)

    svg_parts = []

    # Draw box rectangle
    svg_parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'fill="{fill}" stroke="{BOX_STROKE}" stroke-width="{BOX_STROKE_WIDTH}" '
        f'rx="2" />'
    )

    # Draw text (centered vertically, with padding)
    text_x = x + 5
    text_y = y + h / 2 + TEXT_FONT_SIZE / 3
    escaped_text = _escape_text(text)

    # Note: We don't truncate text to match Max's behavior where text can overflow
    # the box visually. SVG will handle rendering even if text extends beyond box bounds.

    svg_parts.append(
        f'<text x="{text_x}" y="{text_y}" '
        f'font-family="{TEXT_FONT_FAMILY}" font-size="{TEXT_FONT_SIZE}" '
        f'fill="{TEXT_COLOR}">{escaped_text}</text>'
    )

    # Draw inlet/outlet ports if enabled
    if show_ports:
        # Try to get inlet/outlet count via methods (for maxref-enabled boxes)
        inlet_count = 0
        outlet_count = 0

        if hasattr(box, "get_inlet_count"):
            try:
                inlet_count = box.get_inlet_count() or 0
            except Exception:
                pass

        if hasattr(box, "get_outlet_count"):
            try:
                outlet_count = box.get_outlet_count() or 0
            except Exception:
                pass

        # Fallback to private attributes if methods don't exist
        if inlet_count == 0:
            inlet_count = getattr(box, "_inlet_count", 0) or 0
        if outlet_count == 0:
            outlet_count = getattr(box, "_outlet_count", 0) or 0

        # Draw inlets at top, colored by signal vs message/control type.
        if inlet_count > 0:
            inlet_types = _inlet_types(box)
            inlet_spacing = w / (inlet_count + 1)
            for i in range(inlet_count):
                inlet_x = x + inlet_spacing * (i + 1)
                inlet_y = y
                svg_parts.append(
                    f'<circle cx="{inlet_x}" cy="{inlet_y}" r="{PORT_RADIUS}" '
                    f'fill="{_port_color(inlet_types, i)}" '
                    f'stroke="{BOX_STROKE}" stroke-width="0.5" />'
                )

        # Draw outlets at bottom, colored by signal vs message/control type.
        if outlet_count > 0:
            outlet_types = _outlet_types(box)
            outlet_spacing = w / (outlet_count + 1)
            for i in range(outlet_count):
                outlet_x = x + outlet_spacing * (i + 1)
                outlet_y = y + h
                svg_parts.append(
                    f'<circle cx="{outlet_x}" cy="{outlet_y}" r="{PORT_RADIUS}" '
                    f'fill="{_port_color(outlet_types, i)}" '
                    f'stroke="{BOX_STROKE}" stroke-width="0.5" />'
                )

    return "\n".join(svg_parts)


def _get_port_position(
    box: AbstractBox, port_index: int, is_outlet: bool
) -> tuple[float, float]:
    """Calculate the x,y position of an inlet or outlet port."""
    rect = getattr(box, "patching_rect", None)
    if not rect:
        return (0, 0)

    # Handle both Rect objects and list/tuple representations
    if hasattr(rect, "x"):
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
    elif isinstance(rect, (list, tuple)) and len(rect) >= 4:
        x, y, w, h = rect[0], rect[1], rect[2], rect[3]
    else:
        return (0, 0)

    # Try to get port count via methods first
    if is_outlet:
        count = 1
        if hasattr(box, "get_outlet_count"):
            try:
                count = box.get_outlet_count() or 1
            except Exception:
                count = getattr(box, "_outlet_count", 1) or 1
        else:
            count = getattr(box, "_outlet_count", 1) or 1

        spacing = w / (count + 1)
        port_x = x + spacing * (port_index + 1)
        port_y = y + h
    else:
        count = 1
        if hasattr(box, "get_inlet_count"):
            try:
                count = box.get_inlet_count() or 1
            except Exception:
                count = getattr(box, "_inlet_count", 1) or 1
        else:
            count = getattr(box, "_inlet_count", 1) or 1

        spacing = w / (count + 1)
        port_x = x + spacing * (port_index + 1)
        port_y = y

    return (port_x, port_y)


def _render_patchline(line: AbstractPatchline, patcher: Patcher) -> str:
    """Render a patchline connection to SVG."""
    # Get source and destination boxes
    src_id = getattr(line, "src", None)
    dst_id = getattr(line, "dst", None)

    if not src_id or not dst_id:
        return ""

    src_box = patcher._objects.get(src_id)
    dst_box = patcher._objects.get(dst_id)

    if not src_box or not dst_box:
        return ""

    # Get port indices
    source = getattr(line, "source", [src_id, 0])
    destination = getattr(line, "destination", [dst_id, 0])

    src_port = int(source[1]) if len(source) > 1 else 0
    dst_port = int(destination[1]) if len(destination) > 1 else 0

    # Calculate connection points
    x1, y1 = _get_port_position(src_box, src_port, is_outlet=True)
    x2, y2 = _get_port_position(dst_box, dst_port, is_outlet=False)

    # Signal cables (from a signal outlet) are drawn thicker and distinct.
    out_types = _outlet_types(src_box)
    is_signal = src_port < len(out_types) and out_types[src_port] == "signal"
    color = SIGNAL_LINE_COLOR if is_signal else LINE_COLOR
    width = SIGNAL_LINE_WIDTH if is_signal else LINE_WIDTH

    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="{width}" '
        f'stroke-linecap="round" />'
    )


def _calculate_viewbox(patcher: Patcher) -> tuple[float, float, float, float]:
    """Calculate SVG viewBox to fit all objects with padding."""
    boxes = patcher._boxes

    if not boxes:
        return (0, 0, 800, 600)

    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for box in boxes:
        rect = getattr(box, "patching_rect", None)
        if rect:
            # Handle both Rect objects and list/tuple representations
            if hasattr(rect, "x"):
                x, y, w, h = rect.x, rect.y, rect.w, rect.h
            elif isinstance(rect, (list, tuple)) and len(rect) >= 4:
                x, y, w, h = rect[0], rect[1], rect[2], rect[3]
            else:
                continue

            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)

    # Add padding
    min_x -= PADDING
    min_y -= PADDING
    max_x += PADDING
    max_y += PADDING

    width = max_x - min_x
    height = max_y - min_y

    return (min_x, min_y, width, height)


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
    output_path = Path(output_path)

    # Calculate viewBox
    vx, vy, vw, vh = _calculate_viewbox(patcher)

    # Start SVG
    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vx} {vy} {vw} {vh}" '
        f'width="{vw}" height="{vh}">',
        "",
        "<defs>",
        "  <style>",
        "    text { user-select: none; }",
        "  </style>",
        "</defs>",
        "",
        # Max-like patcher background.
        f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="{BG_COLOR}" />',
        "",
    ]

    # Add title if provided
    if title:
        title_y = vy + 20
        svg_parts.extend(
            [
                f'<text x="{vx + vw / 2}" y="{title_y}" '
                f'font-family="{TEXT_FONT_FAMILY}" font-size="16" font-weight="bold" '
                f'fill="{TEXT_COLOR}" text-anchor="middle">{_escape_text(title)}</text>',
                "",
            ]
        )

    # Render patchlines first (so they appear behind boxes)
    svg_parts.append("<!-- Patchlines -->")
    for line in patcher._lines:
        line_svg = _render_patchline(line, patcher)
        if line_svg:
            svg_parts.append(line_svg)
    svg_parts.append("")

    # Render boxes
    svg_parts.append("<!-- Boxes -->")
    for box in patcher._boxes:
        box_svg = _render_box(box, show_ports=show_ports)
        if box_svg:
            svg_parts.append(box_svg)
    svg_parts.append("")

    # Close SVG
    svg_parts.append("</svg>")

    # Write to file
    svg_content = "\n".join(svg_parts)
    output_path.write_text(svg_content, encoding="utf-8")


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
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
        temp_path = Path(f.name)

    try:
        export_svg(patcher, temp_path, show_ports=show_ports, title=title)
        return temp_path.read_text(encoding="utf-8")
    finally:
        temp_path.unlink()


__all__ = ["export_svg", "export_svg_string"]
