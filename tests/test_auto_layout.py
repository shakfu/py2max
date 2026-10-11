"""Patcher(auto_layout=True) lays out on save when boxes or cords changed."""

import json

from py2max import Patcher
from py2max.core.common import Rect

STRICT = {"validate_connections": True}


def _chain(p):
    osc, gain, dac = p.add("cycle~ 440"), p.add("gain~"), p.add("ezdac~")
    p.link(osc, gain)
    p.link(gain, dac)
    p.link(gain, dac, inlet=1)
    return osc, gain, dac


def _saved_xs(path):
    boxes = json.loads(path.read_text())["patcher"]["boxes"]
    return [b["box"]["patching_rect"][0] for b in boxes]


def _spy(monkeypatch):
    calls = []
    orig = Patcher.optimize_layout

    def spy(self, **kw):
        calls.append(self)
        orig(self, **kw)

    monkeypatch.setattr(Patcher, "optimize_layout", spy)
    return calls


def test_save_lays_out(tmp_path):
    path = tmp_path / "auto.maxpat"
    p = Patcher(path, layout="topdown", auto_layout=True, **STRICT)
    _chain(p)
    p.save()
    assert _saved_xs(path) == [48.0, 48.0, 48.0]


def test_off_by_default(tmp_path):
    path = tmp_path / "default.maxpat"
    p = Patcher(path, **STRICT)
    _chain(p)
    p.save()
    assert len(set(_saved_xs(path))) == 2  # ezdac~ stays at its anchor


def test_default_is_topdown_and_optimize_aligns(tmp_path):
    path = tmp_path / "optimized.maxpat"
    p = Patcher(path, **STRICT)
    assert type(p._layout_mgr).__name__ == "TopDownLayoutManager"
    _chain(p)
    p.optimize_layout()
    p.save()
    assert _saved_xs(path) == [48.0, 48.0, 48.0]


def test_unchanged_patch_is_not_laid_out_again(tmp_path, monkeypatch):
    # flow recomputes every position, so a second layout on save would drop
    # the alignment asked for explicitly
    p = Patcher(
        tmp_path / "flow.maxpat",
        layout="flow",
        flow_direction="vertical",
        auto_layout=True,
        **STRICT,
    )
    osc, gain, dac = _chain(p)
    p.optimize_layout(align_ports=True)
    calls = _spy(monkeypatch)
    p.save()
    assert calls == []
    assert osc.patching_rect.x == gain.patching_rect.x == dac.patching_rect.x


def test_manual_move_after_layout_is_kept(tmp_path):
    p = Patcher(tmp_path / "moved.maxpat", layout="topdown", auto_layout=True)
    osc, gain, dac = _chain(p)
    p.optimize_layout()
    dac.patching_rect = Rect(300, 300, 45, 45)
    p.save()
    assert tuple(dac.patching_rect[:2]) == (300, 300)


def test_change_after_layout_lays_out_again(tmp_path, monkeypatch):
    p = Patcher(tmp_path / "grown.maxpat", layout="topdown", auto_layout=True)
    osc, gain, dac = _chain(p)
    p.optimize_layout()
    p.link(osc, dac)
    calls = _spy(monkeypatch)
    p.save()
    assert calls == [p]


def test_subpatcher_inherits_and_is_laid_out(tmp_path, monkeypatch):
    p = Patcher(tmp_path / "parent.maxpat", auto_layout=True, **STRICT)
    sub = p.add_subpatcher("p voice").subpatcher
    assert sub._auto_layout
    _chain(sub)
    calls = _spy(monkeypatch)
    p.save()
    assert sub in calls


def test_loaded_patch_is_not_laid_out(tmp_path, monkeypatch):
    path = tmp_path / "loaded.maxpat"
    p = Patcher(path, **STRICT)
    _chain(p)
    p.save()
    q = Patcher.from_file(path)
    assert q._auto_layout is False
    calls = _spy(monkeypatch)
    q.save()
    assert calls == []


def test_loaded_subpatcher_is_not_laid_out(tmp_path):
    path = tmp_path / "nested.maxpat"
    p = Patcher(path, **STRICT)
    _chain(p.add_subpatcher("p voice").subpatcher)
    p.save()
    sub = Patcher.from_file(path)._boxes[0].subpatcher
    assert sub._auto_layout is False
