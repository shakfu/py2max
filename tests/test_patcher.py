from pathlib import Path

from py2max import Patcher
import json

DATA_DIR = Path(__file__).parent / "data"


def test_patcher_basics():
    p = Patcher("outputs/test_patcher_basics.maxpat", title="top notch patcher")
    assert repr(p) == "Patcher(path='outputs/test_patcher_basics.maxpat')"
    assert p._layout_mgr.parent.rect == p.rect
    osc1 = p.add_textbox("cycle~")
    osc2 = p.add_textbox("cycle~ 440")
    assert osc1.id and osc2.id
    assert repr(osc1) == f"Box(id='{osc1.id}', maxclass='newobj')"
    assert osc1.oid == 1
    line1 = p.add_patchline_by_index(osc1.id, osc2.id)
    assert line1
    assert repr(line1)
    assert len(line1.to_tuple()) == 5
    p.save()


def test_patcher_from_file():
    p = Patcher.from_file(
        DATA_DIR / "complex.maxpat", save_to="outputs/test_complex.maxpat"
    )
    assert len(p._boxes) == len(p.boxes) == 53
    assert len(list(p)) == 60
    assert p.to_json()
    p.save()
    p.save_as("outputs/test_complex2.maxpat")


def test_optimize_layout_forwards_changed_objects():
    """Patcher.optimize_layout() must forward ``changed_objects`` to the layout
    manager so the incremental path is reachable through the public API.

    Regression: the facade previously called ``self._layout_mgr.optimize_layout()``
    with no arguments, silently discarding the change set and always forcing a
    full relayout.
    """
    p = Patcher("outputs/test_optimize_forwarding.maxpat", layout="grid")
    a = p.add_textbox("cycle~ 440")
    b = p.add_textbox("gain~")
    p.add_line(a, b)

    received: list = []
    real = p._layout_mgr.optimize_layout

    def spy(changed_objects=None):
        received.append(changed_objects)
        return real(changed_objects)

    p._layout_mgr.optimize_layout = spy  # type: ignore[method-assign]

    p.optimize_layout()  # full layout
    p.optimize_layout({a.id})  # incremental request

    assert received == [None, {a.id}]


def test_optimize_layout_incremental_leaves_untouched_objects_fixed():
    """A small change set routes through incremental layout, which keeps
    unaffected, unconnected objects at their existing positions."""
    p = Patcher("outputs/test_optimize_incremental.maxpat", layout="grid")
    # Two connected objects plus a pool of disconnected ones so the affected
    # fraction (one object + its neighbour) stays under the incremental threshold.
    a = p.add_textbox("cycle~ 440")
    b = p.add_textbox("gain~")
    p.add_line(a, b)
    others = [p.add_textbox(f"print label{i}") for i in range(12)]

    p.optimize_layout()  # settle everything
    before = {o.id: tuple(o.patching_rect) for o in others}

    assert p._layout_mgr.should_use_incremental({a.id}) is True
    p.optimize_layout({a.id})

    after = {o.id: tuple(o.patching_rect) for o in others}
    assert after == before


def test_patcher_from_file_comparison_complex():
    pd = Patcher.from_file(DATA_DIR / "complex.maxpat").to_dict()
    with open(DATA_DIR / "complex.maxpat") as f:
        d = json.load(f)
    assert pd == d


def test_patcher_from_file_comparison_simple():
    pd = Patcher.from_file(DATA_DIR / "simple.maxpat").to_dict()
    with open(DATA_DIR / "simple.maxpat") as f:
        d = json.load(f)
    assert pd == d
