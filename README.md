# py2max

A pure python library without any dependencies intended to facilitate the offline generation of Max patcher (`.maxpat`) files.

It was originally created to automate the creation of hehlp (`.maxhelp`) files for the [sndpipe project](https://github.com/shakfu/sndpipe) but it seems useful enough that it should have its own repo.

## Possible use cases

- generation of test cases during external development
- takes the pain out of creating parameter objects
- help to save time if you have many objects with slightly different arguments
- use graph drawing algorithms on generated patches
- generative patch generation (-;
- etc..

## Usage examples

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
```


