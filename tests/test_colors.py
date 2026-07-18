from py2max import Patcher


def test_colors():
    p = Patcher("outputs/test_colors.maxpat")
    for i in range(54):
        m = i / 54.0
        p.add_textbox("cycle~ 400", bgcolor=[1.0 - m, 0.32, 0.0 + m, 0.5])
    p.save()

    assert len(p._boxes) == 54
    # each box must emit exactly the bgcolor it was constructed with
    for i, box in enumerate(p._boxes):
        m = i / 54.0
        assert box.to_dict()["box"]["bgcolor"] == [1.0 - m, 0.32, 0.0 + m, 0.5]


def test_set_color():
    p = Patcher("outputs/test_set_color.maxpat")
    box = p.add_textbox("cycle~")
    box.set_color(
        bg=[1.0, 0.0, 0.0, 1.0],
        text=[0.0, 1.0, 0.0, 1.0],
        border=[0.0, 0.0, 1.0, 1.0],
    )
    d = box.to_dict()["box"]
    assert d["bgcolor"] == [1.0, 0.0, 0.0, 1.0]
    assert d["textcolor"] == [0.0, 1.0, 0.0, 1.0]
    assert d["bordercolor"] == [0.0, 0.0, 1.0, 1.0]


def test_apply_theme():
    p = Patcher("outputs/test_apply_theme.maxpat")
    a = p.add_textbox("cycle~")
    b = p.add_textbox("gain~")

    p.apply_theme("dark")
    assert a.to_dict()["box"]["bgcolor"] == [0.15, 0.15, 0.15, 1.0]
    assert b.to_dict()["box"]["bgcolor"] == [0.15, 0.15, 0.15, 1.0]

    # re-theming overrides the previous theme values
    p.apply_theme("light")
    assert a.to_dict()["box"]["bgcolor"] == [0.83, 0.83, 0.83, 1.0]
    assert b.to_dict()["box"]["bgcolor"] == [0.83, 0.83, 0.83, 1.0]
