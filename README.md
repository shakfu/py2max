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


