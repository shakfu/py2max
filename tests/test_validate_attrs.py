"""Tests for maxref-backed keyword-attribute validation (validate_attrs)."""

import warnings

import pytest

from py2max import Patcher


def _warnings_for(build):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        build()
    return [str(w.message) for w in caught if issubclass(w.category, UserWarning)]


def test_validate_attrs_catches_typo():
    msgs = _warnings_for(
        lambda: Patcher(validate_attrs=True).add_floatparam("master", inital=0.5)
    )
    assert any("inital" in m for m in msgs)


def test_validate_attrs_on_by_default():
    msgs = _warnings_for(lambda: Patcher().add_floatparam("x", inital=0.5))
    assert msgs == [
        "Unknown attribute 'inital' for Max object 'flonum' (possible typo?)"
    ]


def test_validate_attrs_can_be_disabled():
    p = Patcher(validate_attrs=False)
    assert _warnings_for(lambda: p.add_floatparam("x", inital=0.5)) == []


def test_validate_attrs_no_false_positives_on_real_attrs():
    def build():
        p = Patcher(validate_attrs=True)
        p.add_textbox("cycle~ 440", frequency=440)  # object-specific attr
        p.add_textbox("gain~", bgcolor=[0, 0, 0, 1])  # universal jbox attr
        p.add_floatparam("amp", 0.5, 0, 1)  # parameter machinery
        p.add_umenu(items="a b c")  # umenu-specific attr
        p.add_message("1 2")
        p.add_comment("hi")
        p.add_subpatcher("p sub")

    assert _warnings_for(build) == []


def test_validate_attrs_skips_unknown_objects():
    # No maxref entry -> cannot validate -> no warning even for odd kwargs.
    msgs = _warnings_for(
        lambda: Patcher(validate_attrs=True).add_textbox(
            "totally.made.up.object", nonsense=1
        )
    )
    assert msgs == []


def test_validate_attrs_flags_unknown_on_known_object():
    msgs = _warnings_for(
        lambda: Patcher(validate_attrs=True).add_textbox("cycle~ 440", wibble=1)
    )
    assert any("wibble" in m and "cycle~" in m for m in msgs)


@pytest.mark.parametrize("flag", [True, False])
def test_validate_attrs_does_not_change_output(flag):
    # Validation is warn-only: the generated patch is identical either way.
    p = Patcher(validate_attrs=flag)
    p.add_textbox("cycle~ 440")
    p.add_textbox("gain~")
    assert len(p._boxes) == 2


# --- @attr text on UI boxes ------------------------------------------------
def test_text_attr_typo_warns_once_by_default():
    msgs = _warnings_for(lambda: Patcher().add_textbox("waveform~ @bufername buf"))
    assert msgs == [
        "Unknown attribute 'bufername' for Max object 'waveform~' (possible typo?)"
    ]


def test_text_attr_typo_warns_once_with_validate_attrs():
    msgs = _warnings_for(
        lambda: Patcher(validate_attrs=True).add_textbox("waveform~ @bufername buf")
    )
    assert len(msgs) == 1


def test_known_text_attrs_do_not_warn():
    msgs = _warnings_for(
        lambda: Patcher().add_textbox(
            "waveform~ @buffername buf @ruler 1 @bgcolor 1 0 0 1"
        )
    )
    assert msgs == []


def test_text_attr_typo_warns_with_validate_attrs_disabled():
    # text attributes escape mypy, so they are checked even when opted out
    msgs = _warnings_for(
        lambda: Patcher(validate_attrs=False).add_textbox("waveform~ @bufername b")
    )
    assert len(msgs) == 1


def test_keyword_attrs_unchecked_when_disabled():
    p = Patcher(validate_attrs=False)
    assert _warnings_for(lambda: p.add_textbox("waveform~", wibble=1)) == []


# --- keys Max saves that maxref omits -----------------------------------------
def _max_written_boxes():
    import json
    from pathlib import Path

    from py2max.maxref import MAXCLASS_DEFAULTS

    def walk(patcher):
        for entry in patcher.get("boxes", []):
            box = entry["box"]
            mc = box.get("maxclass")
            if (MAXCLASS_DEFAULTS.get(mc) or {}).get("maxclass") == mc:
                yield mc, box
            if "patcher" in box:
                yield from walk(box["patcher"])

    for path in sorted(Path(__file__).parent.joinpath("data").glob("*.maxpat")):
        yield from walk(json.loads(path.read_text())["patcher"])


def test_max_written_fixtures_have_no_unknown_attrs():
    from py2max.core.factory import unknown_attrs

    boxes = list(_max_written_boxes())
    assert boxes
    unknown = [(mc, k) for mc, box in boxes for k in unknown_attrs(mc, box)]
    assert unknown == []
