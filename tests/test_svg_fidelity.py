"""Tests for SVG export fidelity improvements (REVIEW.md E2).

Covers honoring user box colors, drawing UI-object affordances, resolving ports
from the box's own numinlets/numoutlets (so it works without maxref and lines
up with patchline endpoints), and the in-memory string export.
"""

from py2max import Patcher
from py2max.core.common import Rect
from py2max.export.svg import _get_port_position, export_svg, export_svg_string


def test_svg_honors_box_colors():
    p = Patcher("x.maxpat")
    # use a text-bearing object so the text color appears in the output
    p.add_textbox("metro 500").set_color(bg="red", border="blue", text="white")
    svg = p.to_svg_string()
    assert "rgb(217,0,0)" in svg  # bgcolor -> red
    assert "rgb(0,0,255)" in svg  # bordercolor -> blue
    assert "rgb(255,255,255)" in svg  # textcolor -> white


def test_svg_draws_ui_affordances():
    p = Patcher("x.maxpat")
    p.add_textbox("toggle")
    p.add_textbox("button")
    p.add_message("bang")
    p.add_floatbox()
    svg = p.to_svg_string()
    assert "<path" in svg  # message flag notch
    assert "<polygon" in svg  # number-box triangle marker
    assert "<circle" in svg  # button glyph and/or ports


def test_svg_ports_use_box_counts_without_maxref():
    p = Patcher("x.maxpat")
    a = p.add_textbox("totallyunknownobj~")  # not in maxref
    a.numinlets, a.numoutlets = 3, 2
    svg = export_svg_string(p)
    # 3 inlets + 2 outlets => at least 5 port circles from this single box
    assert svg.count("<circle") >= 5


def test_svg_patchline_endpoint_matches_drawn_port():
    p = Patcher("x.maxpat")
    a = p.add_textbox("src")
    a.numoutlets = 2
    a.patching_rect = Rect(0.0, 0.0, 90.0, 20.0)
    b = p.add_textbox("dst")
    b.patching_rect = Rect(0.0, 100.0, 90.0, 20.0)
    p.add_line(a, b, outlet=1)
    # outlet 1 of a 2-outlet, 90px-wide box sits at 90 * 2/(2+1) = 60
    x, _ = _get_port_position(a, 1, is_outlet=True)
    assert abs(x - 60.0) < 0.01


def test_export_svg_string_matches_file(tmp_path):
    p = Patcher("x.maxpat")
    p.add_textbox("cycle~ 440")
    p.add_textbox("ezdac~")
    path = tmp_path / "o.svg"
    export_svg(p, path)
    assert export_svg_string(p) == path.read_text(encoding="utf-8")
