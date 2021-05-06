from .. import Patcher


def test_colors():
    p = Patcher('outputs/colors.maxpat')
    for i in range(54):
        m = i/54.
        p.add_textbox('cycle~ 400', bgcolor=[1.0-m, 0.32, 0.0+m, 0.5])
    p.save()


if __name__ == '__main__':
    test_colors()
