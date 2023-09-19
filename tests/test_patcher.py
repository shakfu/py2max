from py2max import Patcher
import json

def test_patcher_basics():
    p = Patcher('outputs/test_patcher_basics.maxpat', title="top notch patcher")
    assert repr(p) == "Patcher(path='outputs/test_patcher_basics.maxpat')"
    assert p._layout_mgr.parent.rect == p.rect
    osc1 = p.add_textbox('cycle~')
    osc2 = p.add_textbox('cycle~ 440')
    assert osc1.id and osc2.id
    assert repr(osc1) == f"Box(id='{osc1.id}', maxclass='newobj')"
    assert osc1.oid == 1
    line1 = p.add_patchline_by_index(osc1.id, osc2.id)
    assert line1
    assert repr(line1)
    assert len(line1.to_tuple()) == 5
    p.save()


def test_patcher_from_file():
    p = Patcher.from_file('tests/data/complex.maxpat', save_to='outputs/test_complex.maxpat')
    assert len(p.boxes) == 53
    assert len(list(p)) == 60
    assert p.to_json()
    p.save()
    p.save_as('outputs/test_complex2.maxpat')

def test_patcher_from_file_comparison_complex():
    pd = Patcher.from_file('tests/data/complex.maxpat').to_dict()
    with open('tests/data/complex.maxpat') as f:
        d = json.load(f)
    assert pd == d


def test_patcher_from_file_comparison_simple():
    pd = Patcher.from_file('tests/data/simple.maxpat').to_dict()
    with open('tests/data/simple.maxpat') as f:
        d = json.load(f)
    assert pd == d

