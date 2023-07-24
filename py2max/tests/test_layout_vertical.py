from ..core import Patcher, VerticalLayoutManager

def test_layout_vertical():
    p = Patcher('outputs/test_layout_vertical.maxpat', 
                layout_mgr_class=VerticalLayoutManager)

    x = None
    for i in range(20):
        if not x:
            x = p.add_floatbox()
            continue
        y = p.add_floatbox()
        p.link(x, y)
        x = y

    p.save()


if __name__ == '__main__':
    test_layout_vertical()
