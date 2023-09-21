
from py2max import Patcher



def test_bpatcher():
    # create bpatcher
    bp = Patcher(path='outputs/test_bpatcher_child.maxpat', openinpresentation=1)
    in1 = bp.add('inlet')
    scope = bp.add('scope~', presentation=1,
                   presentation_rect=[4.0, 4.0, 130.0, 130.0])
    bp.link(in1, scope)
    bp.save()

    # create parent patcher
    p = Patcher(path='outputs/test_bpatcher_parent.maxpat')
    osc = p.add('cycle~ 2')
    bp2 = p.add_bpatcher('test_bpatcher_child',
        patching_rect=[32.0, 92.0, 140.0, 140.0])
    dac = p.add('ezdac~')
    p.link(osc, bp2)
    p.save()

