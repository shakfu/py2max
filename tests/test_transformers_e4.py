"""Regression tests for the E4 transformer work (REVIEW.md E4).

- run_pipeline now delegates to compose (compose is no longer dead).
- add-comment's position argument is reachable through the CLI value syntax.
- two new transformers: apply-theme and scale-positions.
"""

from py2max import Patcher
from py2max.transformers import (
    available_transformers,
    compose,
    create_transformer,
    run_pipeline,
)


def _patch(*specs: str) -> Patcher:
    p = Patcher("x.maxpat")
    for spec in specs:
        p.add_textbox(spec)
    return p


def test_new_transformers_registered():
    names = available_transformers()
    assert "apply-theme" in names
    assert "scale-positions" in names


def test_scale_positions_moves_but_keeps_size():
    p = _patch("cycle~ 440", "gain~")
    before = [tuple(b.patching_rect) for b in p._boxes]
    run_pipeline(p, [create_transformer("scale-positions", "2.0")])
    for b, (x, y, w, h) in zip(p._boxes, before):
        assert b.patching_rect[0] == x * 2 and b.patching_rect[1] == y * 2
        assert b.patching_rect[2] == w and b.patching_rect[3] == h  # sizes unchanged


def test_apply_theme_sets_colors():
    p = _patch("toggle")
    create_transformer("apply-theme", "dark")(p)
    assert p._boxes[0]._kwds.get("bgcolor") is not None


def test_add_comment_position_prefix_is_reachable():
    p = _patch("metro 500")
    box = p._boxes[0]
    create_transformer("add-comment", "below:tempo")(p)
    comment = next(b for b in p._boxes if b.maxclass == "comment")
    assert comment.text == "tempo"
    assert comment.patching_rect[1] > box.patching_rect[1]  # placed 'below'


def test_add_comment_non_position_colon_preserved():
    p = _patch("dac~")
    create_transformer("add-comment", "note: hi")(p)
    comment = next(b for b in p._boxes if b.maxclass == "comment")
    assert comment.text == "note: hi"  # default 'above', text intact


def test_run_pipeline_matches_compose():
    p1, p2 = _patch("cycle~ 440"), _patch("cycle~ 440")
    t = create_transformer("scale-positions", "1.5")
    run_pipeline(p1, [t])
    compose([t])(p2)
    assert [tuple(b.patching_rect) for b in p1._boxes] == [
        tuple(b.patching_rect) for b in p2._boxes
    ]
