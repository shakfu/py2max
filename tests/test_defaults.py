from py2max import Patcher


def test_defaults():
    p = Patcher(path='outputs/test_defaults.maxpat')
    for i in range(10):
        p.add(f'cycle~ {i*20}')
    p.add_textbox('filtergraph~')
    p.add_textbox('scope~')
    p.add_textbox('ezdac~')
    p.save()

