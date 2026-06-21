"""Tests for color/theme helpers (resolve_color, Box.set_color, apply_theme)."""

import pytest

from py2max import Patcher
from py2max.core.colors import MAX_COLORS, THEMES, resolve_color


def test_resolve_color_named():
    assert resolve_color("red") == [0.85, 0.0, 0.0, 1.0]
    assert resolve_color("WHITE") == [1.0, 1.0, 1.0, 1.0]  # case-insensitive
    # returns a copy, not the shared palette entry
    assert resolve_color("black") is not MAX_COLORS["black"]


def test_resolve_color_hex():
    assert resolve_color("#000000") == [0.0, 0.0, 0.0, 1.0]
    assert resolve_color("#ffffff") == [1.0, 1.0, 1.0, 1.0]
    rgba = resolve_color("#ff8800")
    assert rgba[0] == 1.0 and rgba[3] == 1.0
    # 8-digit hex includes alpha
    assert resolve_color("#00000080")[3] == pytest.approx(128 / 255)


def test_resolve_color_sequence():
    assert resolve_color([0.2, 0.4, 0.6]) == [0.2, 0.4, 0.6, 1.0]  # alpha appended
    assert resolve_color([0.1, 0.2, 0.3, 0.5]) == [0.1, 0.2, 0.3, 0.5]


def test_resolve_color_errors():
    with pytest.raises(ValueError):
        resolve_color("notacolor")
    with pytest.raises(ValueError):
        resolve_color("#xyz")
    with pytest.raises(ValueError):
        resolve_color([0.1, 0.2])  # too few components


def test_box_set_color_chaining_and_attrs():
    p = Patcher("outputs/theme_box.maxpat")
    box = p.add_textbox("toggle").set_color(bg="blue", text="white", border="#333333")
    assert box._kwds["bgcolor"] == [0.0, 0.0, 1.0, 1.0]
    assert box._kwds["textcolor"] == [1.0, 1.0, 1.0, 1.0]
    assert box._kwds["bordercolor"][0] == pytest.approx(0x33 / 255)


def test_box_set_color_returns_self():
    p = Patcher("outputs/theme_box2.maxpat")
    box = p.add_textbox("gain~")
    assert box.set_color(bg="gray") is box


@pytest.mark.parametrize("theme", sorted(THEMES))
def test_apply_named_theme_colors_every_box(theme):
    p = Patcher("outputs/theme_all.maxpat")
    p.add_textbox("cycle~ 440")
    p.add_textbox("gain~")
    returned = p.apply_theme(theme)
    assert returned is p  # chainable
    assert all("bgcolor" in b._kwds for b in p._boxes)
    assert all("textcolor" in b._kwds for b in p._boxes)


def test_apply_theme_recurses_into_subpatchers():
    p = Patcher("outputs/theme_sub.maxpat")
    sub_box = p.add_subpatcher("p voice")
    sub_box.subpatcher.add_textbox("cycle~ 440")
    p.apply_theme("dark")
    inner = sub_box.subpatcher._boxes[0]
    assert "bgcolor" in inner._kwds


def test_apply_theme_dict():
    p = Patcher("outputs/theme_dict.maxpat")
    p.add_textbox("gain~")
    p.apply_theme({"bg": "red", "text": "white"})
    assert p._boxes[0]._kwds["bgcolor"] == [0.85, 0.0, 0.0, 1.0]


def test_apply_theme_unknown_raises():
    p = Patcher("outputs/theme_bad.maxpat")
    with pytest.raises(ValueError):
        p.apply_theme("chartreuse-deluxe")


def test_theme_round_trips():
    p = Patcher("outputs/theme_rt.maxpat")
    p.add_textbox("cycle~ 440")
    p.apply_theme("blue")
    p.save()
    reloaded = Patcher.from_file("outputs/theme_rt.maxpat")
    box = reloaded._boxes[0]
    bgcolor = box._kwds.get("bgcolor") or getattr(box, "bgcolor", None)
    assert bgcolor is not None
