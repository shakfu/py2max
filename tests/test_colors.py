from py2max import Patcher


def test_colors():
    p = Patcher(path='outputs/test_colors.maxpat')
    for i in range(54):
        m = i/54.
        p.add_box('cycle~ 400', bgcolor=[1.0-m, 0.32, 0.0+m, 0.5])
    p.save()

