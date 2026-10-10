"""add_textbox: argument-aware port counts and UI box routing."""

import pytest

from py2max import Patcher
from py2max.core.common import Rect
from py2max.maxref import porttypes


@pytest.mark.parametrize(
    "text,n_in,n_out",
    [
        ("route phase info", 3, 3),
        ("unpack 0. 0 0 0. 0. 0. 0", 1, 7),
        ("sel 0 1 2 3", 5, 5),
        ("t f f", 1, 2),
        ("trigger b i l", 1, 3),
        ("pack 0 0 0", 3, 1),
    ],
)
def test_declared_counts_follow_arguments(text, n_in, n_out):
    box = Patcher().add_textbox(text)
    d = box.to_dict()["box"]
    assert (d["numinlets"], d["numoutlets"]) == (n_in, n_out)
    assert len(d["outlettype"]) == n_out
    assert d["maxclass"] == "newobj" and d["text"] == text


@pytest.mark.parametrize("text", ["t f f", "route phase info", "sel 0 1 2 3"])
def test_declared_outlets_agree_with_port_counts(text):
    box = Patcher().add_textbox(text)
    assert box.numoutlets == porttypes.port_counts(text.split()[0], text)[1]


def test_explicit_counts_win():
    box = Patcher().add_textbox("route a b", numoutlets=5)
    assert box.numoutlets == 5
    assert len(box.to_dict()["box"]["outlettype"]) == 5


def test_validation_accepts_argument_outlets():
    p = Patcher(validate_connections=True)
    route = p.add_textbox("route phase info")
    p.add_line(route, p.add_textbox("print"), outlet=2)
    assert route.numoutlets == 3


@pytest.mark.parametrize(
    "name", ["flonum", "number", "waveform~", "ezdac~", "umenu", "live.dial"]
)
def test_ui_objects_get_their_box_form(name):
    d = Patcher().add_textbox(name).to_dict()["box"]
    assert d["maxclass"] == name
    assert "text" not in d


@pytest.mark.parametrize("name", ["cycle~ 440", "jit.window", "live.colors"])
def test_non_ui_objects_stay_newobj(name):
    d = Patcher().add_textbox(name).to_dict()["box"]
    assert d["maxclass"] == "newobj"
    assert d["text"] == name


@pytest.mark.parametrize("name", ["message", "comment"])
def test_text_boxes_keep_their_content(name):
    d = Patcher().add_textbox(f"{name} hello world").to_dict()["box"]
    assert d["maxclass"] == name
    assert d["text"] == "hello world"


def test_ui_object_positional_arguments_are_dropped_with_warning(caplog):
    d = Patcher().add_textbox("flonum 3").to_dict()["box"]
    assert "text" not in d
    assert "ignoring arguments ['3']" in caplog.text


def test_ui_object_attr_arguments_become_box_attributes(caplog):
    d = Patcher().add_textbox("waveform~ @buffername buf").to_dict()["box"]
    assert d["buffername"] == "buf"
    assert "text" not in d
    assert "ignoring" not in caplog.text


def test_ui_object_attr_values_are_typed(recwarn):
    d = (
        Patcher()
        .add_textbox("live.dial @parameter_enable 1 @activedialcolor 1 0 0 1")
        .to_dict()["box"]
    )
    assert d["parameter_enable"] == 1 and isinstance(d["parameter_enable"], int)
    assert d["activedialcolor"] == [1, 0, 0, 1]
    assert not recwarn.list


def test_ui_object_positionals_before_attrs_are_dropped(caplog):
    d = Patcher().add_textbox("waveform~ buf @buffername other").to_dict()["box"]
    assert d["buffername"] == "other"
    assert "ignoring arguments ['buf']" in caplog.text


def test_keyword_argument_overrides_attr_text():
    box = Patcher().add_textbox("waveform~ @buffername a", buffername="b")
    assert box.to_dict()["box"]["buffername"] == "b"


def test_newobj_attr_text_is_left_in_text():
    d = Patcher().add_textbox("metro 500 @active 1").to_dict()["box"]
    assert d["text"] == "metro 500 @active 1"
    assert "active" not in d


@pytest.mark.parametrize("name,n_in,n_out", [("inlet", 0, 1), ("outlet", 1, 0)])
def test_inlet_outlet_port_counts(name, n_in, n_out):
    d = Patcher().add_textbox(name).to_dict()["box"]
    assert (d["maxclass"], d["numinlets"], d["numoutlets"]) == (name, n_in, n_out)


# --- box width from text --------------------------------------------------------
@pytest.mark.parametrize(
    "text,max_width",
    # widths Max gave these boxes in Max-written patches
    [
        ("cycle~ 1", 53.0),
        ("faustgen~", 64.0),
        ("selector~ 3", 70.0),
        ("prepend freq015", 99.0),
        ("buffer~ latencyBuff 1000 3", 150.0),
    ],
)
def test_object_width_follows_text(text, max_width):
    box = Patcher().add_textbox(text)
    assert box.patching_rect[2] == pytest.approx(max_width, abs=3.0)


def test_width_covers_many_ports():
    box = Patcher().add_textbox("unpack 0 0 0 0 0 0 0 0 0 0")
    assert box.patching_rect[2] >= 15.0 * box.numoutlets


def test_message_width_follows_text():
    p = Patcher()
    assert p.add_message("polyphony 8").patching_rect[2] == pytest.approx(75.0, abs=3.0)
    assert p.add_textbox("message read foo.dsp").patching_rect[2] == pytest.approx(
        77.0, abs=3.0
    )


def test_explicit_rect_width_is_kept():
    box = Patcher().add_textbox("cycle~ 440", patching_rect=Rect(0.0, 0.0, 200.0, 22.0))
    assert box.patching_rect[2] == 200.0


@pytest.mark.parametrize("name", ["live.dial", "gain~", "toggle"])
def test_ui_box_keeps_its_default_size(name):
    from py2max.maxref import MAXCLASS_DEFAULTS

    default = MAXCLASS_DEFAULTS[name]["patching_rect"]
    rect = Patcher().add_textbox(name).patching_rect
    assert (rect[2], rect[3]) == (default.w, default.h)
