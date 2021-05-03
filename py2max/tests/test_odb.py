from .. import Patcher


def test_odb():
    p = Patcher('output/odb.maxpat')
    fg = p.add_textbox('filtergraph~')
    scop = p.add_textbox('scope~')
    p.save()


if __name__ == '__main__':
    test_odb()
