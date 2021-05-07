from .. import Patcher


def test_defaults():
    p = Patcher('outputs/test_defaults.maxpat')
    p.add_textbox('filtergraph~')
    p.add_textbox('scope~')
    p.save()


if __name__ == '__main__':
    test_defaults()
