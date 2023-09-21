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



