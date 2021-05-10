# py2max

A pure python library without any dependencies intended to facilitate the offline generation of Max patcher (`.maxpat`) files.

It was originally created to automate the creation of help (`.maxhelp`) files for the [sndpipe project](https://github.com/shakfu/sndpipe) but it seems useful enough that it should have its own repo.

For use of python3 in a live Max patcher, see the [py-js](https://github.com/shakfu/py-js) project.

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

By default objects are returned (including patchlines). While returned objects are useful for linking, the returned patchlines are not. With aliases (for `.add_textbox` and `.add_line`) the above can be written in a more abbreviated form:

```python
p = MaxPatch('out.maxpat')
osc = p.add('cycle~ 440')
gain = p.add('gain~')
dac = p.add('ezdac~')
p.link(osc, gain)
p.link(gain, dac)
p.save()
```

You can parse existing `.maxpat` files, change them and then save the changes:

```python3
p = Patcher.from_file('example1.maxpat')
# ... make some change
p.saveas('example1_mod.maxpat)
```

And you can create different Max objects including subpatchers:

```python
p = Patcher('out.maxpat')
sbox = p.add_subpatcher('p mysub')
sp = sbox.subpatcher
in1 = sp.add('inlet')
gain = sp.add('gain~')
out1 = sp.add('outlet')
osc = p.add('cycle~ 440')
dac = p.add('ezdac~')
sp.link(in1, gain)
sp.link(gain, out1)
p.link(osc, sbox)
p.link(sbox, dac)
p.save()
```

In general, almost all Max/MSP and Jitter objects can be added to the patcher file with the `.add_textbox` or `.add` method. There are specialized methods for numbers and also for numeric parameters. 

In addition, objects which have their own `maxclass` may have their own corresponding Python class or method to provide specialized features. For example, the `.add_coll` method allows one to add a python dictionary which is then embedded in the patcher file which can be quite useful.

Further tests are in the `py2max/tests` folder and can be output to an `outputs` folder all at once by running `pytest` in the project root, or individually, by doing something like the following:

```bash
python3 -m pytest.tests.test_basic
```

## Caveats

- The current layout algorithm is extremely rudimentary at this stage, however there are some [promising directions](docs/notes/graph-drawing.md) to address this. In practice, you will necessarily have to move most things around after generation.

- While generation does not consume the py2max objects, Max does not unfortunately refresh-from-file when it's open, so you will have to keep closing and reopening Max to see the changes to the object tree.
