# py2max

A pure python3 library without dependencies intended to facilitate the offline generation of Max patcher files (`.maxpat`, `.maxhelp`, `.rbnopat`).

If you are looking for python3 externals for Max/MSP check out the [py-js](https://github.com/shakfu/py-js) project.

## Features

- Scripted *offline* generation of Max patcher files using Python objects, corresponding, on a one-to-one basis, with Max/MSP objects stored in the `.maxpat` JSON-based file format.

- *Round-trip conversion* between (JSON) `.maxpat` files with arbitrary levels of nesting and corresponding `Patcher`, `Box`, and `Patchline` Python objects.

- Can potentially handle any Max object or maxclass.

- Lots of unit tests, ~99% coverage.

- Analysis and offline scripted modification of Max patches in terms of composition, structure (as graphs of objects), object properties and layout (using graph-drawing algorithms).

- Allows precise layout and configuration of Max objects.

- `Patcher` objects have generic methods such as `add_textbox` and can also have specialized methods such as `add_coll`. As an example, this method has a `dictionary` argument to make it easy to prepopulate the `coll` object (see `py2max/tests/test_coll.py`).

- Provides a `maxclassdb` feature which recalls default configurations of Max Objects.

## Possible use cases

- Scripted patcher file creation.

- Batch modification of existing .maxpat files.

- Use the rich python standard library and ecosystem to help create parametrizable objects with configuration from offline sources. For example, one-of-a-kind wavetable oscillators configured from random wavetable files.

- Generation of test cases and `.maxhelp` files during external development

- Takes the pain out of creating objects with lots of parameters

- Prepopulate containers objects such as `coll`, `dict` and `table` objects with data

- Help to save time creating many objects with slightly different arguments

- Use [graph drawing / layout algorithms](docs/auto-layouts.md) on generated patches.

- Generative patch generation `(-;`

- etc..

## Usage examples

```python
p = Patcher('my-patch.maxpat')
osc1 = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
dac = p.add_textbox('ezdac~')
osc1_gain = p.add_line(osc1, gain)
gain_dac0 = p.add_line(gain, outlet=0, dac, inlet=0)
gain_dac1 = p.add_line(gain, outlet=0, dac, inlet=1)
p.save()
```

By default, objects are returned (including patchlines), and patchline outlets and inlets are set to 0. While returned objects are useful for linking, the returned patchlines are not. Therefore, the above can be written more concisely as:

```python
p = Patcher('my-patch.maxpat')
osc1 = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
dac = p.add_textbox('ezdac~')
p.add_line(osc1, gain)
p.add_line(gain, dac)
p.add_line(gain, dac, inlet=1)
p.save()
```

With builtin aliases (`.add` for `.add_*`  type methods and `.link` for `.add_line`), the above example can be written in an even more abbreviated form (and with a vertical layout) as:

```python
p = Patcher('out_vertical.maxpat', layout='vertical')
osc = p.add('cycle~ 440')
gain = p.add('gain~')
dac = p.add('ezdac~')
p.link(osc, gain)
p.link(gain, dac)
p.link(gain, dac, 1)
p.save()
```

In addition, you can parse existing `.maxpat` files, change them and then save the changes:

```python
p = Patcher.from_file('example1.maxpat')
# ... make some change
p.save_as('example1_mod.maxpat')
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

## Installation

Simplest way:

```bash
git https://github.com/shakfu/py2max.git
cd py2max
pip install . # optional
```

Note that py2max does not need to be installed to be used, so you can skip the `pip install .` part if you prefer and just `cd` into the cloned directory and start using it:

```bash
$ cd py2max
$ ipython

In [1]: from py2max import Patcher

In [2]: p = Patcher.from_file("tests/data/simple.maxpat")

In [3]: p._boxes
Out[3]: [Box(id='obj-2', maxclass='ezdac~'), Box(id='obj-1', maxclass='newobj')]
```

## Testing

`py2max` has an extensive test suite with tests are in the `py2max/tests` folder.

One can run all tests as follows:

```bash
pytest
```

This will output the results of all tests into `outputs` folder.

Note that some tests may be skipped if a required package for the test cannot be imported.

You can check which test is skipped by the following:

```bash
pytest -v
```

To check test coverage:

```bash
./scripts/coverage.sh
```

which essentially does the following

```bash
mkdir -p outputs
pytest --cov-report html:outputs/_covhtml --cov=py2max tests
```

To run an individual test:

```bash
python3 -m pytest tests.test_basic
```

Note that because `py2max` primarily deals with `json` generation and manipulation, most tests have no dependencies since `json` is already built into the stdlib.

However, a bunch of tests explore the application of orthogonal graph layout algorithms and for this, a whole bunch of packages have been used, which range from the well-known to the esoteric.

As mentioned above, pytest will skip a test if required packages are not installed, so these are entirely optional tests.

If you insist on diving into the rabbit hole, and want to run all tests you will need the following packages (and their dependencies):

- [networkx](https://networkx.org): `pip install networkx`
- [matplotlib](<https://matplotlib.org>): `pip install matplotlib`
- [pygraphviz](https://github.com/pygraphviz/pygraphviz): Pygraphviz requires installing the development library of graphviz: <https://www.graphviz.org/> (On macOS this can be done via `brew install graphviz`) -- then you can `pip install pygraphviz`
- [adaptagrams](https://github.com/mjwybrow/adaptagrams): First build the adaptagrams c++ libs and then build the swig-based python wrapper.
- [pyhola](https://github.com/shakfu): a pybind11 wrapper of adaptagrams. Follow build instructions in the README and install from the git repo.
- [tsmpy](https://github.com/uknfire/tsmpy): install from git repo
- [OrthogonalDrawing](https://github.com/hasii2011/OrthogonalDrawing): install from git repo

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

The project has a few of scripts which may be useful:

- `convert.py`: convert `maxpat` to `yaml` for ease of reading during dev
- `compare.py`: compare using [deepdiff](https://zepworks.com/deepdiff/current/diff.html)
- `coverage.sh`: run pytest coverage and generate html coverage report

Note that if you want to build py2max as a wheel:

```bash
pip install build
cd py2max
python3 -m build .
```

The wheel then should be in the `dist` directory.

## Examples of Use

- [Generate Max patchers for faust2rnbo](https://github.com/grame-cncm/faust/blob/master-dev/architecture/max-msp/rnbo.py)

## Credits and Licensing

All rights reserved to the original respective authors:

- Steve Kieffer, Tim Dwyer, Kim Marriott, and Michael Wybrow. HOLA: Human-like Orthogonal Network Layout. In Visualization and Computer Graphics, IEEE Transactions on, Volume 22, Issue 1, pages 349 - 358. IEEE, 2016. DOI

- Aric A. Hagberg, Daniel A. Schult and Pieter J. Swart, “Exploring network structure, dynamics, and function using NetworkX”, in Proceedings of the 7th Python in Science Conference (SciPy2008), Gäel Varoquaux, Travis Vaught, and Jarrod Millman (Eds), (Pasadena, CA USA), pp. 11–15, Aug 2008

- A Technique for Drawing Directed Graphs Emden R. Gansner, Eleftherios Koutsofios, Stephen C. North, Kiem-phong Vo • IEEE TRANSACTIONS ON SOFTWARE ENGINEERING • Published 1993

- Gansner, E.R., Koren, Y., North, S. (2005). Graph Drawing by Stress Majorization. In: Pach, J. (eds) Graph Drawing. GD 2004. Lecture Notes in Computer Science, vol 3383. Springer, Berlin, Heidelberg. <https://doi.org/10.1007/978-3-540-31843-9_25>

- An open graph visualization system and its applications to software engineering Emden R. Gansner, Stephen C. North • SOFTWARE - PRACTICE AND EXPERIENCE • Published 2000
