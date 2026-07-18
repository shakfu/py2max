"""Regression tests for LayoutManager.prevent_overlaps (REVIEW.md L6).

The previous symmetric pairwise pusher clamped boxes back inside the canvas and
oscillated -- it never converged on dense clusters. The sweep-based resolver
pushes each object clear of already-placed ones (monotone), so it converges,
early-exits when nothing overlaps, and preserves each object's real size.
"""

import pytest

from py2max import Patcher
from py2max.core.common import Rect


def _count_overlaps(boxes, gap):
    n = 0
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            ra, rb = a.patching_rect, b.patching_rect
            if (
                ra.x < rb.x + rb.w + gap
                and rb.x < ra.x + ra.w + gap
                and ra.y < rb.y + rb.h + gap
                and rb.y < ra.y + ra.h + gap
            ):
                n += 1
    return n


def _stack(offset, n=12, w=60.0, h=22.0):
    p = Patcher("overlap.maxpat")
    for i in range(n):
        b = p.add_textbox(f"o{i}")
        b.patching_rect = Rect(100.0 + i * offset[0], 100.0 + i * offset[1], w, h)
    return p


@pytest.mark.parametrize(
    "offset", [(0, 0), (8, 6), (20, 0), (15, 15)], ids=["stacked", "cascade", "row", "grid"]
)
def test_prevent_overlaps_converges(offset):
    p = _stack(offset)
    gap = 10.0
    assert _count_overlaps(p._boxes, gap) > 0  # starts overlapping
    iters = p._layout_mgr.prevent_overlaps(min_gap=gap)
    assert _count_overlaps(p._boxes, gap) == 0  # converged to zero overlaps
    assert iters < 50  # well under the iteration cap (i.e. did not spin out)


def test_prevent_overlaps_preserves_dimensions():
    p = _stack((8, 6))
    p._layout_mgr.prevent_overlaps(min_gap=10.0)
    assert all(
        b.patching_rect.w == 60.0 and b.patching_rect.h == 22.0 for b in p._boxes
    )


def test_prevent_overlaps_is_noop_when_already_separated():
    p = Patcher("sep.maxpat")
    for i in range(6):
        b = p.add_textbox(f"o{i}")
        b.patching_rect = Rect(100.0 + i * 100, 100.0, 60.0, 22.0)
    before = [tuple(b.patching_rect) for b in p._boxes]
    iters = p._layout_mgr.prevent_overlaps(min_gap=10.0)
    assert iters == 1  # a single pass with no moves
    assert [tuple(b.patching_rect) for b in p._boxes] == before  # positions unchanged
