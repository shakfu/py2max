# py2max

A pure python library without dependencies intended to facilitate the offline generation of Max patcher (`.maxpat`) files.

It was created to automate the creation of help (`.maxhelp`) files for the [sndpipe project](https://github.com/shakfu/sndpipe) but it seems useful enough that it should have its own repo.

For the use of python3 in a live Max patcher, check out a bunch of python3 externals at the [py-js](https://github.com/shakfu/py-js) project.

## Features

- Offline scripted generation of max patcher files using Python objects corresponding, on a one-to-one basis, with MAX objects stored in the `.maxpat` JSON format.

- Round-trip conversion between (JSON) `.maxpat` files with arbitrary levels of nesting and corresponding `Patcher`, `Box`, and `Patchline` Python objects.

- Can handle potentially any Max object or maxclass.

- Lots of unit tests.

- Analysis and offline scripted modification of Max patches in terms of composition, structure (as graphs of objects), object properties and layout (in the context of graph-drawing algorithms).

- Allows precise layout and configuration of Max objects.

- Patcher objects have generic methods such as `add_textbox` and can also have specialized methods such as `add_coll`. In the latter case, for example, the `add_coll` method has a `dictionary` argument to make it easy to prepopulate the `coll` object (see `py2max/tests/test_coll.py`).

- Has a `maxclassdb` feature which recalls default configuration of Max Objects.

## Possible use cases

- Create parametrizable objects with configuration from offline sources. For example, one-of-a-kind wavetable oscillators configured from random wavetable files.

- Generation of test cases during external development

- Takes the pain out of creating objects with lots of parameters

- Prepopulate containers objects such as `coll`, `dict` and `table` objects with data

- Help to save time creating many objects with slightly different arguments

- Use graph drawing algorithms on generated patches

- Generative patch generation (-;

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

By default objects are returned (including patchlines). While returned objects are useful for linking, the returned patchlines are not.

With builtin aliases (for `.add_textbox` and `.add_line`), and knowing that the default outgoing outlet number and incoming inlet number is automatically set to 0, the above example can be written in a more abbreviated form:

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

Another example with subpatchers:

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

Note that Python classes are basically just simple wrappers around the JSON structures in a .maxpat file, and almost all Max/MSP and Jitter objects can be added to the patcher file with the `.add_textbox` or the generic `.add` methods. There are also specialized methods in the form `.add_<type>` for numbers, numeric parameters, subpatchers, and container-type objects (see the design notes below for more details).

Further tests are in the `py2max/tests` folder and can be output to an `outputs` folder all at once by running `pytest` in the project root, or individually, by doing something like the following:

```bash
python3 -m pytest tests.test_basic
```

## Caveats

- API Docs are still not available

- The current default layout algorithm is extremely rudimentary, however there are some [promising directions](docs/notes/graph-drawing.md) and you can see also see a [visual comparison](docs/auto-layouts.md) of how well different layout algorithms perform in this context.

- While generation does not consume the py2max objects, Max does not unfortunately refresh-from-file when it's open, so you will have to keep closing and reopening Max to see the changes to the object tree.

- For the few objects which have their own methods, the current implementation differentiates tilde objects from non-tilde objects by providing a different method with a `_tilde` suffix:

	```python
	gen = p.add_gen()

	gen_tilde = p.add_gen_tilde()
	```

## Design Notes

The `.maxpat` JSON format is actually pretty minimal and hierarchical. It has a parent `Patcher` and child `Box` entries and also `Patchlines`. Certain boxes contain other `patcher` instances to represent nested subpatchers and `gen~` patches, etc..

The above structure directly maps onto the Python implementation which consists of 3 classes: `Patcher`, `Box`, and `Patchline`. These classes are extendable via their respective `**kwds` and internal`__dict__` structures. In fact, this is the how the `.from_file` patcher classmethod is implemented.

This turns out to be the most maintainable and flexible way to handle all the differences between the hundreds of Max, MSP, and Jitter objects.

A growing list of patcher methods have been implemented to specialize and facilitate the creation of certain classes of objects which require additional configuration:

- `.add_attr`
- `.add_beap`
- `.add_bpatcher`
- `.add_codebox`
- `.add_coll`
- `.add_comment`
- `.add_dict`
- `.add_floatbox`
- `.add_floatparam`
- `.add_gen`
- `.add_intbox`
- `.add_intparam`
- `.add_itable`
- `.add_message`
- `.add_rnbo`
- `.add_subpatcher`
- `.add_table`
- `.add_textbox`
- `.add_umenu`

This is a short list, but the `add_textbox` method alone can handle almost all case. The others are really just there for convenience and to save typing.

Generally, it is recommended to start using `py2max`'s via these `add_<type>` methods, since they have most of the required parameters built into the methods and you can get IDE completion support.  Once you are comfortable with the parameters, then use the generic abbreviated form: `add`, which is less typing but tbe tradeoff is you lose the IDE parameter completion support.

## Scripts

The project has a couple of scripts to help with analyzing .maxpat patterns:

- `convert.py`: convert maxpat to yaml for ease of reading during dev
- `compary.py`: compare using [deepdiff](https://zepworks.com/deepdiff/current/diff.html)


## Credits and Licensing

All rights reserved to the original respective authors:

> Steve Kieffer, Tim Dwyer, Kim Marriott, and Michael Wybrow. HOLA: Human-like Orthogonal Network Layout. In Visualization and Computer Graphics, IEEE Transactions on, Volume 22, Issue 1, pages 349 - 358. IEEE, 2016. DOI

> Aric A. Hagberg, Daniel A. Schult and Pieter J. Swart, “Exploring network structure, dynamics, and function using NetworkX”, in Proceedings of the 7th Python in Science Conference (SciPy2008), Gäel Varoquaux, Travis Vaught, and Jarrod Millman (Eds), (Pasadena, CA USA), pp. 11–15, Aug 2008

> A Technique for Drawing Directed Graphs
Emden R. Gansner, Eleftherios Koutsofios, Stephen C. North, Kiem-phong Vo • IEEE TRANSACTIONS ON SOFTWARE ENGINEERING • Published 1993

> Gansner, E.R., Koren, Y., North, S. (2005). Graph Drawing by Stress Majorization. In: Pach, J. (eds) Graph Drawing. GD 2004. Lecture Notes in Computer Science, vol 3383. Springer, Berlin, Heidelberg. https://doi.org/10.1007/978-3-540-31843-9_25

> An open graph visualization system and its applications to software engineering
Emden R. Gansner, Stephen C. North • SOFTWARE - PRACTICE AND EXPERIENCE • Published 2000

The py2max code is placed in the public domain by its author.

