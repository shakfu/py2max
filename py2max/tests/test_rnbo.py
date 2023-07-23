from py2max import *

p = Patcher('outputs/test_rnbo.maxpat')
sbox = p.add_rnbo()
sp = sbox.subpatcher

in1 = sp.add_textbox('in~ 1')
in2 = sp.add_textbox('in~ 2')

out1 = sp.add_textbox('out~ 1')
out2 = sp.add_textbox('out~ 2')

sp.add_line(in1, out1)
sp.add_line(in2, out2)
p.save()

