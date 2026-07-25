from pathlib import Path

from py2max import Patcher
import json
import pytest

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


def test_optimize_layout_is_batch_only():
    """``optimize_layout`` is a batch, whole-patch operation that takes no
    arguments.

    Interactive, per-edit ("incremental") relayout was intentionally removed
    from py2max; it belongs to the editor/server that owns the live editing
    session (see docs/auto-layout.md in py2max-server). Passing a change set is
    therefore a TypeError, at both the facade and the layout-manager level.
    """
    p = Patcher("outputs/test_optimize_batch_only.maxpat", layout="grid")
    a = p.add_textbox("cycle~ 440")
    b = p.add_textbox("gain~")
    p.add_line(a, b)

    # The batch call arranges every object and must not raise.
    p.optimize_layout()
    assert a.patching_rect and b.patching_rect

    # The removed incremental API is gone at both levels.
    with pytest.raises(TypeError):
        p.optimize_layout({a.id})  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        p._layout_mgr.optimize_layout({a.id})  # type: ignore[call-arg]

    # The incremental helpers no longer exist on the layout manager.
    assert not hasattr(p._layout_mgr, "should_use_incremental")
    assert not hasattr(p._layout_mgr, "_incremental_layout")


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
