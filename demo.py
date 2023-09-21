from py2max import Patcher

p = Patcher(path="outputs/model.maxpat")
osc = p.add("cycle~ 440")
dac = p.add("ezdac~")
p.link(osc, dac)
p.link(osc, dac, inlet=1)
p.save()

roundtrip = Patcher.model_validate(p.model_dump(), strict=True)
simple = Patcher.from_file('tests/data/simple.maxpat')
complex = Patcher.from_file('tests/data/complex.maxpat')
complex.save_as("outputs/test_pydant_complex.maxpat")

nested = Patcher.from_file("tests/data/nested.maxpat")


p = Patcher(path='outputs/test_subpatch.maxpat')
sbox = p.add_subpatcher('p mysub')
sp = sbox.subpatcher
i = sp.add_textbox('inlet')
g = sp.add_textbox('gain~')
o = sp.add_textbox('outlet')
osc = p.add_textbox('cycle~ 440')
dac = p.add_textbox('ezdac~')
sp.add_line(i, g)
sp.add_line(g, o)
p.add_line(osc, sbox)
p.add_line(sbox, dac)
p.save()

