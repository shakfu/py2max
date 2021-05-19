# py2max

A pure python library without any dependencies intended to facilitate the offline generation of Max patcher (`.maxpat`) files.

It was created to automate the creation of help (`.maxhelp`) files for the [sndpipe project](https://github.com/shakfu/sndpipe) but it seems useful enough that it should have its own repo.

For use of python3 in a live Max patcher, see the [py-js](https://github.com/shakfu/py-js) project.

## Features

- Offline scripted generation of max patchers files from the ground up using Python objects which correspond, on a one-to-one basis, with MAX objects stored in the `.maxpat` JSON format.

- Round-trip conversion between (JSON) `.maxpat` files with arbitrary levels of nesting and corresponding `Patcher`, `Box`, and `Patchline` Python objects.

- Can handle potentially any Max object or maxclass.

- Lots of unit tests.

- Analysis and offline scripted modification of Max patches in terms of composition, structure (as graphs of objects), object properties and layout (in the context of graph-drawing algorithms).

- Allows precise layout and configuration of Max objects.

- Patcher objects have generic methods such as `add_textbox` and can have specialized methods as required such as `add_coll`. In the latter case, the method makes to prepopulate the `coll` object from a python dictionary (see `py2max/tests/test_coll.py`).

- Has a `maxclassdb` feature which recalls defaults configuration of Max Objects.

## Possible use cases

- create parametrizable objects with configuration from offline sources. For example, one-of-a-kind wavetable oscillators configured from random wavetable files.

- generation of test cases during external development

- takes the pain out of creating parameter objects

- prepopulate containers objects such as `coll`, `dict` and `table` objects with data

- help to save time creating many objects with slightly different arguments

- use graph drawing algorithms on generated patches

- generative patch generation (-;

- etc..

## Usage examples

```python
p = Patcher('out.maxpat')
osc1 = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
dac = p.add_textbox('ezdac~')
osc1_gain = p.add_line(osc1, gain)
gain_dac0 = p.add_line(gain, outlet=0, dac, inlet=0)
gain_dac1 = p.add_line(gain, outlet=0, dac, inlet=1)
p.save()
```

By default objects are returned (including patchlines). While returned objects are useful for linking, the returned patchlines are typically not. With builtin aliases (for `.add_textbox` and `.add_line`), and knowing that the default outgoing outlet number and incoming inlet number set to 0, the above can be written in a more abbreviated form:

```python
p = Patcher('out.maxpat')
osc = p.add('cycle~ 440')
gain = p.add('gain~')
dac = p.add('ezdac~')
p.link(osc, gain)
p.link(gain, dac)
p.link(gain, dac, 1)
p.save()
```

You can parse existing `.maxpat` files, change them and then save the changes:

```python3
p = Patcher.from_file('example1.maxpat')
# ... make some change
p.saveas('example1_mod.maxpat)
```

You can also easily create different Max objects including subpatchers:

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

The Python classes are basically just simple wrappers around their corresponding JSON spec the .maxpat file, almost all Max/MSP and Jitter objects can be added to the patcher file with the `.add_textbox` or the generic `.add` methods. There are also specialized methods in the form `.add_<type>` for numbers, numeric parameters, subpatchers, and container-type objects (see the design notes below for more details).

Further tests are in the `py2max/tests` folder and can be output to an `outputs` folder all at once by running `pytest` in the project root, or individually, by doing something like the following:

```bash
python3 -m pytest.tests.test_basic
```

## Caveats

- API Docs are still not available

- The current layout algorithm is extremely rudimentary, however there are some [promising directions](docs/notes/graph-drawing.md) to address this. In practice, you will necessarily have to move most things around after generation.

- While generation does not consume the py2max objects, Max does not unfortunately refresh-from-file when it's open, so you will have to keep closing and reopening Max to see the changes to the object tree.

- For those objects which have their own methods, the current implementation still has to address cases when two max objects are the same except for '~' symbol.

## Design Notes

The `.maxpat` JSON format is actually pretty minimal and hierarchical. It has a parent `Patcher` and child `Box` entries and also `Patchlines`. Certain boxes contain other `patcher` instances to represent nested subpatchers and `gen~` patches, etc..

The above structure directly maps onto the Python implementation which consists of 3 classes: `Patcher`, `Box`, and `Patchline`. These classes are extendable via their respective `**kwds` and internal`__dict__` structures. In fact, this is the how the `.from_file` patcher classmethod is implemented.

This turns out to be the most maintainable and flexible way to handle all the differences between the hundreds of Max, MSP, and Jitter objects.

Certain patcher methods are implementated to specialize and ease the creation of certain classes of objects:

- `.add_textbox`
- `.add_message`
- `.add_comment`
- `.add_intbox`
- `.add_floatbox`
- `.add_intparam`
- `.add_floatparam`
- `.add_subpatcher`
- `.add_gen`
- `.add_coll`
- `.add_dict`
- `.add_table`
- `.add_itable`
- `.add_umenu`
- `.add_bpatcher`
- `.add_beap`

This is a short list, but the `add_textbox` method alone can handle almost all case. The others are really just there for convenience and to save typing.

Generally, it is recommended to start using `py2max`'s via these `add_<type>` methods, since they have most of the required parameters built into the methods and you can get IDE completion support.  Once you are comfortable with the parameters, then use the generic abbreviated form: `add`, which is less typing but you lose the IDE parameter completion support.
