from py2max import Patcher
from py2max.common import Rect


def test_layout():
    p = Patcher()
    rect = p._layout_mgr.patcher_rect
    assert isinstance(rect, Rect)
    maxclasses = ["filtergraph~", "ezdac~", "ezadc~"]
    for mc in maxclasses:
        r = p._layout_mgr.get_pos(maxclass=mc)
        assert isinstance(r, Rect)
