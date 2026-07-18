"""Tests for editing loaded patches and the box/line removal API.

Covers the P0 correctness fixes:
- C1: from_dict restores id/edge counters so post-load edits don't collide.
- C2: remove_box / remove_line / disconnect.
- C3: add_coll/add_dict/add_table keep a caller's text when name is None.
- C4: add_beap strips the ``.maxpat`` suffix, not a character set.
- C6: patchline order is per-pair and survives intervening links / loads.
- C7: associated comments are emitted via save_as / to_json, not only save.
- C8: an object with no maxref entry still gets an outlet.
"""

import json
from pathlib import Path

from py2max import Patcher

DATA_DIR = Path(__file__).parent / "data"


# --- C1: edit after load ---------------------------------------------------


def test_from_file_restores_id_counter():
    p = Patcher.from_file(DATA_DIR / "simple.maxpat")
    existing = [b.id for b in p._boxes]
    new = p.add("cycle~ 999")
    assert new.id not in existing
    assert p._id_counter == max(
        int(bid.split("-")[1]) for bid in existing + [new.id]
    )


def test_from_file_restores_node_and_edge_indexes():
    p = Patcher.from_file(DATA_DIR / "simple.maxpat")
    assert p._node_ids == [b.id for b in p._boxes]
    assert p._edge_ids == [(ln.src, ln.dst) for ln in p._lines]
    # A post-load add extends the node index rather than desyncing it.
    new = p.add("gain~")
    assert p._node_ids[-1] == new.id


def test_edit_after_load_round_trips(tmp_path):
    p = Patcher.from_file(DATA_DIR / "simple.maxpat")
    n_boxes = len(p._boxes)
    p.add("cycle~ 220")
    out = tmp_path / "edited.maxpat"
    p.save_as(out)
    d = json.load(open(out))
    ids = [b["box"]["id"] for b in d["patcher"]["boxes"]]
    assert len(ids) == n_boxes + 1
    assert len(ids) == len(set(ids)), "duplicate ids after edit-and-save"


def test_from_file_restores_semantic_counter(tmp_path):
    p = Patcher(tmp_path / "s.maxpat", semantic_ids=True)
    p.add("cycle~ 440")  # cycle_1
    p.add("cycle~ 220")  # cycle_2
    p.save()
    reloaded = Patcher.from_file(tmp_path / "s.maxpat")
    reloaded._semantic_ids = True
    nxt = reloaded.add("cycle~ 110")
    assert nxt.id == "cycle_3"


# --- C2: removal API -------------------------------------------------------


def test_disconnect_removes_matching_line():
    p = Patcher("outputs/test_disconnect.maxpat")
    a, b = p.add("cycle~ 440"), p.add("gain~")
    p.link(a, b)
    assert len(p._lines) == 1
    removed = p.disconnect(a, b)
    assert removed == 1
    assert p._lines == []
    assert p._edge_ids == []


def test_disconnect_returns_zero_when_no_match():
    p = Patcher("outputs/test_disconnect0.maxpat")
    a, b = p.add("cycle~ 440"), p.add("gain~")
    assert p.disconnect(a, b) == 0


def test_remove_box_drops_incident_lines_and_indexes():
    p = Patcher("outputs/test_remove_box.maxpat")
    a, b, c = p.add("cycle~ 440"), p.add("gain~"), p.add("ezdac~")
    p.link(a, b)
    p.link(b, c)
    removed = p.remove_box(b)
    assert removed is b
    assert b not in p._boxes
    assert b.id not in p._objects
    assert b.id not in p._node_ids
    # both lines touched b, so both are gone
    assert p._lines == []
    assert p._edge_ids == []


def test_remove_box_by_id():
    p = Patcher("outputs/test_remove_by_id.maxpat")
    a = p.add("cycle~ 440")
    assert p.remove_box(a.id) is a
    assert a.id not in p._objects


def test_remove_box_absent_returns_none():
    p = Patcher("outputs/test_remove_absent.maxpat")
    assert p.remove_box("nonexistent") is None


def test_remove_box_drops_pending_comment():
    p = Patcher("outputs/test_remove_comment.maxpat")
    a = p.add("cycle~ 440", comment="osc")
    assert any(pc[0] == a.id for pc in p._pending_comments)
    p.remove_box(a)
    assert not any(pc[0] == a.id for pc in p._pending_comments)


def test_remove_alias():
    p = Patcher("outputs/test_remove_alias.maxpat")
    a = p.add("cycle~ 440")
    assert p.remove(a) is a


# --- C5: subpatcher round-trip fidelity ------------------------------------


def _iter_nested_patchers(patcher_dict):
    """Yield every nested subpatcher dict within a top-level patcher dict."""
    for box_wrap in patcher_dict.get("boxes", []):
        box = box_wrap["box"]
        if "patcher" in box:
            yield box["patcher"]
            yield from _iter_nested_patchers(box["patcher"])


def test_nested_roundtrip_is_byte_identical():
    orig = json.load(open(DATA_DIR / "nested.maxpat"))
    p = Patcher.from_dict(orig["patcher"])
    assert p.to_dict() == orig, "nested patch is not round-trip faithful"


def test_complex_roundtrip_is_byte_identical():
    orig = json.load(open(DATA_DIR / "complex.maxpat"))
    p = Patcher.from_dict(orig["patcher"])
    assert p.to_dict() == orig, "complex patch is not round-trip faithful"


def test_subpatchers_do_not_gain_top_level_keys():
    orig = json.load(open(DATA_DIR / "nested.maxpat"))
    p = Patcher.from_dict(orig["patcher"])
    out = p.to_dict()
    # top-level keeps its own autosave/dependency_cache
    assert "autosave" in out["patcher"]
    assert "dependency_cache" in out["patcher"]
    # nested subpatchers (which never had them) must not acquire them
    nested = list(_iter_nested_patchers(out["patcher"]))
    assert nested, "fixture should contain subpatchers"
    for sub in nested:
        assert "autosave" not in sub
        assert "dependency_cache" not in sub


# --- replace: swap a box in place, preserving position and wiring ----------


def test_replace_preserves_wiring_and_position(tmp_path):
    p = Patcher(tmp_path / "r.maxpat")
    osc = p.add("cycle~ 440")
    gain = p.add("gain~")
    p.link(osc, gain)
    orig_rect = list(osc.patching_rect)

    saw = p.replace(osc, "saw~ 220")

    assert osc.id not in p._objects
    assert saw.id in p._objects
    assert saw.text == "saw~ 220"
    # the single a->b line now originates from the replacement
    assert len(p._lines) == 1
    assert p._lines[0].src == saw.id
    assert p._lines[0].dst == gain.id
    assert p._edge_ids == [(saw.id, gain.id)]
    # window position (x, y) inherited from the replaced box
    assert list(saw.patching_rect)[:2] == orig_rect[:2]


def test_replace_keeps_slot_ordering(tmp_path):
    p = Patcher(tmp_path / "r2.maxpat")
    a = p.add("cycle~ 440")
    b = p.add("gain~")
    c = p.add("ezdac~")
    idx = p._boxes.index(b)
    new = p.replace(b, "lores~ 1000")
    assert p._boxes[idx] is new
    assert p._boxes.count(new) == 1
    assert [box.id for box in p._boxes] == [a.id, new.id, c.id]
    assert p._node_ids == [a.id, new.id, c.id]


def test_replace_preserves_incoming_and_outgoing(tmp_path):
    p = Patcher(tmp_path / "r3.maxpat")
    src = p.add("cycle~ 440")
    mid = p.add("gain~")
    dst = p.add("ezdac~")
    p.link(src, mid)
    p.link(mid, dst)
    new = p.replace(mid, "lores~ 1000")
    srcs_dsts = {(pl.src, pl.dst) for pl in p._lines}
    assert srcs_dsts == {(src.id, new.id), (new.id, dst.id)}


def test_replace_with_prebuilt_box(tmp_path):
    from py2max.core.box import Box

    p = Patcher(tmp_path / "r4.maxpat")
    osc = p.add("cycle~ 440")
    gain = p.add("gain~")
    p.link(osc, gain)
    replacement = Box(id="custom-1", maxclass="newobj", text="saw~ 110")
    result = p.replace(osc, replacement)
    assert result is replacement
    assert result.id == "custom-1"
    assert p._lines[0].src == "custom-1"


def test_replace_transfers_pending_comment(tmp_path):
    p = Patcher(tmp_path / "r5.maxpat")
    osc = p.add("cycle~ 440", comment="the oscillator")
    new = p.replace(osc, "saw~ 220")
    assert any(pc[0] == new.id for pc in p._pending_comments)
    assert not any(pc[0] == osc.id for pc in p._pending_comments)


def test_replace_unknown_raises(tmp_path):
    import pytest

    p = Patcher(tmp_path / "r6.maxpat")
    with pytest.raises(KeyError):
        p.replace("nonexistent", "gain~")


def test_replace_round_trips(tmp_path):
    p = Patcher(tmp_path / "r7.maxpat")
    osc = p.add("cycle~ 440")
    gain = p.add("gain~")
    p.link(osc, gain)
    p.replace(osc, "saw~ 220")
    out = tmp_path / "replaced.maxpat"
    p.save_as(out)
    d = json.load(open(out))
    ids = [b["box"]["id"] for b in d["patcher"]["boxes"]]
    assert len(ids) == len(set(ids)), "duplicate ids after replace"
    texts = [b["box"].get("text") for b in d["patcher"]["boxes"]]
    assert "saw~ 220" in texts
    assert "cycle~ 440" not in texts


# --- C3: coll/dict/table text preservation ---------------------------------


def test_add_coll_keeps_text_without_name():
    p = Patcher("outputs/test_coll_text.maxpat")
    box = p.add_coll(text="coll shared @embed 1")
    assert box.text == "coll shared @embed 1"


def test_add_dict_keeps_text_without_name():
    p = Patcher("outputs/test_dict_text.maxpat")
    box = p.add_dict(text="dict shared @embed 1")
    assert box.text == "dict shared @embed 1"


def test_add_table_keeps_text_without_name():
    p = Patcher("outputs/test_table_text.maxpat")
    box = p.add_table(text="table shared @embed 1")
    assert box.text == "table shared @embed 1"


def test_add_coll_default_text_with_name():
    p = Patcher("outputs/test_coll_name.maxpat")
    box = p.add_coll(name="mydata")
    assert box.text == "coll mydata @embed 1"


# --- C4: add_beap suffix handling ------------------------------------------


def test_add_beap_strips_only_suffix():
    p = Patcher("outputs/test_beap.maxpat")
    # 'map.maxpat': str.rstrip('.maxpat') would strip the trailing char set
    # {'.','m','a','x','p','t'} and yield '' -- removesuffix keeps 'map'.
    box = p.add_beap("map.maxpat")
    assert box.to_dict()["box"]["varname"] == "map"


def test_add_beap_without_suffix_unchanged():
    p = Patcher("outputs/test_beap2.maxpat")
    box = p.add_beap("drums")
    assert box.to_dict()["box"]["varname"] == "drums"


# --- C6: patchline order ---------------------------------------------------


def test_patchline_order_survives_intervening_link():
    p = Patcher("outputs/test_order.maxpat")
    a, b, c = p.add("cycle~ 440"), p.add("gain~"), p.add("ezdac~")
    l1 = p.link(a, b)
    p.link(a, c)  # different pair, intervening
    l2 = p.link(a, b)  # second a->b wire
    assert l1.to_dict()["patchline"]["order"] == 0
    assert l2.to_dict()["patchline"]["order"] == 1


def test_patchline_order_continues_after_load(tmp_path):
    p = Patcher(tmp_path / "order.maxpat")
    a, b = p.add("cycle~ 440"), p.add("gain~")
    p.link(a, b)
    p.save()

    reloaded = Patcher.from_file(tmp_path / "order.maxpat")
    src = reloaded.find_by_id("obj-1")
    dst = reloaded.find_by_id("obj-2")
    line = reloaded.add_line(src, dst)
    assert line.to_dict()["patchline"]["order"] == 1


# --- C7: comments emitted on all save paths --------------------------------


def test_comment_emitted_via_to_json():
    p = Patcher("outputs/test_comment_json.maxpat")
    p.add("cycle~ 440", comment="my oscillator")
    assert "my oscillator" in p.to_json()


def test_comment_emitted_via_save_as(tmp_path):
    p = Patcher(tmp_path / "c.maxpat")
    p.add("cycle~ 440", comment="labelled")
    out = tmp_path / "with_comment.maxpat"
    p.save_as(out)
    assert "labelled" in out.read_text()


# --- C8: unknown object outlets --------------------------------------------


def test_unknown_object_has_outlet():
    p = Patcher("outputs/test_unknown.maxpat")
    box = p.add_textbox("some_unknown_object~ 42")
    assert box.numoutlets == 1


def test_unknown_object_can_be_connection_source():
    p = Patcher("outputs/test_unknown_src.maxpat")
    src = p.add_textbox("some_unknown_object~")
    dst = p.add("gain~")
    line = p.add_line(src, dst)  # would be meaningless with 0 outlets
    assert line.src == src.id
