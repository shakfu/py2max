# py2max

A pure python library without any dependencies intended to facilitate the offline generation of Max patcher (.maxpat) files.

It was originally created to automate the creation of .maxhelp files for the
[sndpipe project](https://github.com/shakfu/sndpipe) but it seems useful enough
that it should have its own repo.

Usage example:

```python
p = MaxPatch('out.maxpat')
osc1 = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
dac = p.add_textbox('ezdac~')
osc1_gain = p.add_line(osc1, gain)
gain_dac = p.add_line(gain, dac)
p.save()
```

By default objects are returned (including patchlines which can be ignored as below).

And you can even create subpatchers:

```python
p = Patcher('out.maxpat')
sp, sbox = p.add_subpatcher('p mysub')
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
```

For the case of subpatchers, note that `.add_subpatcher` returns a tuple of two objects: the (sub)Patcher object  and the subpatcher's textbox.

