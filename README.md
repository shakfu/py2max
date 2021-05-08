# py2max

A pure python library without any dependencies intended to facilitate the offline generation of Max patcher (`.maxpat`) files.

It was originally created to automate the creation of hehlp (`.maxhelp`) files for the [sndpipe project](https://github.com/shakfu/sndpipe) but it seems useful enough that it should have its own repo.

## Features

- Round-trip conversion between `.maxpat` and Python `Patcher` objects.

- Offline scripted generation of max patchers files using Python objects which correspond, on a one-to-one basic, with MAX objects stored in the `.maxpat` JSON format.

- Allows precise layout and configuration of Max objects.

- Patcher objects have generic methods such as `add_textbox` and can have specialized methods as required such as `add_coll`. In the latter case, the method makes to prepopulate the `coll` object from a python dictionary (see `py2max/tests/test_coll.py`).

- Has a `maxclassdb` feature which recalls defaults configuration of Max Objects.

## Current Status

## Possible use cases

- create parametrizable objects with configuration from offline sources. For example, one-of-a-kind wavetable oscillators configured from random wavetable files.
- generation of test cases during external development
- takes the pain out of creating parameter objects
- prepopulate a `coll` object with data
- help to save time creating many objects with slightly different arguments
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

Further tests are in the `py2max/tests` folder and can be output to an `output` folder all at once by running `pytest` in the project root, or individually, by doing something like the following:

```bash
python3 -m pytest.tests.test_basic
```

## Caveats

- The layout algorithm is extremely rudimentary at this stage. So you will necessarily have to most things around after generation.

- While generation does not consume the py2max objects so changes can be made and the patcher file resaved from a terminal or ipython session, Max does not unfortunately refresh-from-file when it's open, so you will have to keep closing and reopening Max to see the changes. As some consolation, it is possible to generate a live matplotlib graph of the patcher by using Networkx (see test_graph.py in the `tests` subfolder).

## TODO

- Implement more objects: especially object with state stored in the `.maxpat` file.

- Anchor certain objects in expected places in the grid:
  - ezadc~ to top left
  - ezdac~ to bottom left
  - visualization object (scope, etc.) to bottom right

- Parsing of .maxpat files to python objects -- would require rename py2max to py4max to signify py2max and max2py.

- Convert patchlines to references (send/receive)
