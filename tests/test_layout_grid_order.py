"""Grid optimize_layout() places boxes in signal order, not creation order."""

from py2max import Patcher
from py2max.core.common import Rect


def _xy(box):
    return tuple(box.patching_rect[:2])


def _abstraction(order):
    p = Patcher("outputs/grid_order.maxpat", layout="grid", flow_direction="vertical")
    boxes = {name: p.add_textbox(name) for name in order}
    p.add_line(boxes["inlet"], boxes["*~ 0.5"])
    p.add_line(boxes["*~ 0.5"], boxes["outlet"])
    return p, boxes


def test_out_of_order_creation_is_sorted_by_signal():
    p, b = _abstraction(["inlet", "outlet", "*~ 0.5"])
    p.optimize_layout()
    ys = [_xy(b[n])[1] for n in ("inlet", "*~ 0.5", "outlet")]
    assert ys == sorted(ys) and len(set(ys)) == 3


def test_signal_ordered_patch_is_unchanged():
    p, b = _abstraction(["inlet", "*~ 0.5", "outlet"])
    before = [_xy(x) for x in p._boxes]
    p.optimize_layout()
    assert [_xy(x) for x in p._boxes] == before


def test_horizontal_flow_sorts_left_to_right():
    p = Patcher("outputs/grid_order_h.maxpat", layout="grid")
    dac = p.add("dac~")
    osc = p.add("cycle~ 440")
    p.add_line(osc, dac)
    p.optimize_layout()
    assert _xy(osc)[0] < _xy(dac)[0]


def test_explicit_rect_is_not_moved():
    p = Patcher("outputs/grid_order_explicit.maxpat", layout="grid")
    dac = p.add("dac~", patching_rect=Rect(400, 300, 45, 22))
    gain = p.add("gain~")
    osc = p.add("cycle~ 440")
    p.add_line(osc, gain)
    p.add_line(gain, dac)
    p.optimize_layout()
    assert _xy(dac) == (400, 300)
    assert _xy(osc)[0] < _xy(gain)[0]


def test_port_order_is_preserved():
    # outlet 2 comes first in signal order; optimize_layout's port-order
    # restore must still keep outlet 1 left of outlet 2
    p = Patcher("outputs/grid_order_ports.maxpat", layout="grid")
    inlet = p.add("inlet")
    out1 = p.add("outlet")
    out2 = p.add("outlet")
    mul = p.add("*~ 0.5")
    p.add_line(inlet, out2)
    p.add_line(inlet, mul)
    p.add_line(mul, out1)
    p.optimize_layout()
    assert _xy(out1)[0] < _xy(out2)[0]


def test_clustered_order_follows_signal():
    p = Patcher(
        "outputs/grid_order_cluster.maxpat",
        layout="grid",
        flow_direction="vertical",
        cluster_connected=True,
    )
    dac = p.add("dac~")
    osc = p.add("cycle~ 440")
    p.add_line(osc, dac)
    p.optimize_layout()
    assert _xy(osc)[1] < _xy(dac)[1]


def test_signal_order_off_keeps_creation_order():
    for layout, kw in (
        ("grid", {}),
        ("vertical", {}),
        ("grid", {"cluster_connected": True}),
    ):
        p = Patcher(
            "outputs/grid_order_off.maxpat",
            layout=layout,
            flow_direction="vertical",
            signal_order=False,
            **kw,
        )
        boxes = {n: p.add_textbox(n) for n in ("inlet", "outlet", "*~ 0.5")}
        p.add_line(boxes["inlet"], boxes["*~ 0.5"])
        p.add_line(boxes["*~ 0.5"], boxes["outlet"])
        p.optimize_layout()
        ys = [_xy(boxes[n])[1] for n in ("inlet", "outlet", "*~ 0.5")]
        assert ys == sorted(ys) and len(set(ys)) == 3, (layout, kw)
