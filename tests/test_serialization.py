"""Serialization entry points return the patcher as it stands.

`Patcher.to_dict()` used to return a patcher with **no boxes** until something
else happened to call `render()`, and the same call on the same object then
started returning them. That is worse than an empty result: it is
order-dependent, so a test asserting over `to_dict()` examined an empty patcher
and passed for the wrong reason -- which is how it was found, while writing
`test_no_nulls_anywhere_in_a_representative_patch`.

These pin the two properties that make that impossible: `to_dict()` renders on
its own behalf, and `render()` is idempotent so doing it twice cannot duplicate
anything.
"""

import json

import pytest

from py2max import Patcher


@pytest.fixture
def patch(tmp_path):
    """Two boxes and a cord, with nothing rendered yet."""
    p = Patcher(str(tmp_path / "s.maxpat"))
    osc = p.add_textbox("cycle~ 440")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc, dac)
    return p


class TestToDictIsSelfSufficient:
    def test_a_fresh_patcher_serializes_its_boxes(self, patch):
        # The defect: this returned {"boxes": [], "lines": []} on a patcher
        # holding two boxes and a cord.
        d = patch.to_dict()["patcher"]

        assert len(d["boxes"]) == 2
        assert len(d["lines"]) == 1

    def test_the_same_call_gives_the_same_answer_every_time(self, patch):
        # Order-independence is the real property. The old behaviour returned
        # nothing, then started returning boxes once anything else rendered.
        first = patch.to_dict()
        assert [patch.to_dict() for _ in range(3)] == [first] * 3

    def test_rendering_first_by_hand_changes_nothing(self, patch):
        before = patch.to_dict()
        patch.render()
        assert patch.to_dict() == before

    def test_to_json_and_to_dict_agree(self, patch):
        # Modulo Rect, which is a NamedTuple and so becomes a JSON list.
        emitted = json.loads(patch.to_json())["patcher"]
        direct = patch.to_dict()["patcher"]

        assert len(emitted["boxes"]) == len(direct["boxes"])
        assert [e["box"]["text"] for e in emitted["boxes"]] == [
            b["box"]["text"] for b in direct["boxes"]
        ]

    def test_to_json_still_works_when_called_first(self, patch):
        # `to_json` no longer renders on its own -- `to_dict` does it -- so this
        # guards against the render being dropped from both.
        assert len(json.loads(patch.to_json())["patcher"]["boxes"]) == 2

    def test_a_box_added_after_a_render_still_appears(self, patch):
        patch.to_dict()
        patch.add_textbox("gain~")

        assert len(patch.to_dict()["patcher"]["boxes"]) == 3


class TestRenderIsIdempotent:
    def test_rendering_twice_does_not_duplicate_boxes(self, patch):
        patch.render()
        patch.render()
        patch.render()

        assert len(patch.boxes) == 2
        assert len(patch.lines) == 1

    def test_idempotent_even_without_reset_on_render(self, tmp_path):
        # The only path that reached the append: `self.boxes` was appended to
        # while `self.lines` was rebuilt, so a second render duplicated every
        # box and no line. Nothing in the repository passes this flag, which is
        # why it had never bitten.
        p = Patcher(str(tmp_path / "n.maxpat"), reset_on_render=False)
        p.add_textbox("cycle~ 440")

        p.render()
        p.render()

        assert len(p.boxes) == 1

    def test_saving_twice_writes_the_same_patch(self, tmp_path):
        # `save_as` renders for its own log line and `to_dict` renders again
        # underneath it, so this is the round trip that idempotence protects.
        path = tmp_path / "twice.maxpat"
        p = Patcher(str(path))
        p.add_textbox("cycle~ 440")
        p.add_textbox("ezdac~")

        p.save_as(path)
        first = path.read_text()
        p.save_as(path)

        assert path.read_text() == first
        assert len(json.loads(first)["patcher"]["boxes"]) == 2


class TestSubpatchers:
    def test_a_nested_patcher_serializes_without_an_explicit_render(self, tmp_path):
        p = Patcher(str(tmp_path / "sub.maxpat"))
        sp = p.add_subpatcher("p voice")
        sp.subpatcher.add_textbox("cycle~ 220")

        box = p.to_dict()["patcher"]["boxes"][0]["box"]

        assert len(box["patcher"]["boxes"]) == 1

    def test_a_subpatcher_is_not_duplicated_by_repeated_serialization(self, tmp_path):
        p = Patcher(str(tmp_path / "sub2.maxpat"))
        sp = p.add_subpatcher("p voice")
        sp.subpatcher.add_textbox("cycle~ 220")

        p.to_dict()
        box = p.to_dict()["patcher"]["boxes"][0]["box"]

        assert len(box["patcher"]["boxes"]) == 1
