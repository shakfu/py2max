"""Graph layout backends via the built-in GraphLayoutManager.

Exercises every ``layout="graph:*"`` variant end-to-end and writes a separate
output patch per algorithm (``outputs/test_layout_graph_<algo>.maxpat``).

The variants are pulled from ``GraphLayoutManager.ALGORITHMS`` so this test
covers whatever the production manager supports. Each backend is an optional
package (hola-graph / graph-layout / ogdf-py); a variant whose backend is not
installed is skipped rather than failing.
"""

import math

import pytest

from py2max import Patcher
from py2max.layout.external import GraphLayoutManager


def _overlap(a, b):
    """True if rects ``a`` and ``b`` (x, y, w, h) intersect."""
    return (
        a[0] < b[0] + b[2]
        and b[0] < a[0] + a[2]
        and a[1] < b[1] + b[3]
        and b[1] < a[1] + a[3]
    )


def _build_example(p):
    """Two-voice signal graph shared by every layout variant."""
    fbox = p.add_floatbox
    ibox = p.add_intbox
    tbox = p.add_textbox
    link = p.add_line

    freq1 = fbox()
    freq2 = fbox()
    phase = fbox()
    osc1 = tbox("cycle~")
    osc2 = tbox("cycle~")
    amp1 = fbox()
    amp2 = fbox()
    mul1 = tbox("*~")
    mul2 = tbox("*~")
    add1 = tbox("+~")
    dac = tbox("ezdac~")
    scop = tbox("scope~")
    scp1 = ibox()
    scp2 = ibox()

    link(freq1, osc1)
    link(osc1, mul1)
    link(mul1, add1)
    link(amp1, mul1, inlet=1)
    link(freq2, osc2)
    link(phase, osc2, inlet=1)
    link(osc2, mul2)
    link(amp2, mul2, inlet=1)
    link(mul2, add1, inlet=1)
    link(add1, dac)
    link(add1, dac, inlet=1)
    link(add1, scop)
    link(scp1, scop)
    link(scp2, scop, inlet=1)


@pytest.mark.parametrize("algorithm", GraphLayoutManager.ALGORITHMS)
def test_graph_layout_variant(algorithm):
    p = Patcher(
        f"outputs/test_layout_graph_{algorithm}.maxpat",
        layout=f"graph:{algorithm}",
    )
    _build_example(p)
    assert len(p._boxes) == 14
    assert len(p._lines) == 14
    before = [tuple(b.patching_rect)[:2] for b in p._boxes]

    try:
        p.optimize_layout()
    except ImportError as exc:
        # optional backend package (hola-graph / graph-layout / ogdf-py) absent
        pytest.skip(str(exc))
    p.save()

    rects = [tuple(b.patching_rect) for b in p._boxes]
    after = [(x, y) for x, y, _, _ in rects]

    # every box gets a finite coordinate...
    assert all(math.isfinite(x) and math.isfinite(y) for x, y in after)
    # ...is moved off the initial add-time grid...
    assert after != before
    # ...stays on-screen with a non-negative origin (_normalize)...
    assert all(x >= 0 and y >= 0 for x, y in after)
    # ...fits entirely within the patcher window (grown to fit in _full_layout)...
    _, _, win_w, win_h = tuple(p.rect)
    assert all(x + w <= win_w and y + h <= win_h for x, y, w, h in rects)
    # ...and overlaps nothing (prevent_overlaps safety net in _full_layout).
    assert not any(
        _overlap(rects[i], rects[j])
        for i in range(len(rects))
        for j in range(i + 1, len(rects))
    )
