from py2max import Patcher

p = Patcher(path="outputs/model.maxpat")
osc = p.add("cycle~ 440")
dac = p.add("ezdac~")
p.link(osc, dac)
p.link(osc, dac, inlet=1)
p.save()

p1 = Patcher.model_validate(p.model_dump(), strict=True)

p2 = Patcher.from_file('tests/data/simple.maxpat')

