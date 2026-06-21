# py2max Package

The top-level `py2max` package exports the main classes for creating Max/MSP
patcher files.

## Main classes

- [`Patcher`](core.md) -- create and manipulate Max patches
- [`Box`](core.md) -- an individual Max object in a patch
- [`Patchline`](core.md) -- a connection between objects

```python
from py2max import Patcher

p = Patcher('example.maxpat')
osc = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~ 0.5')
dac = p.add_textbox('ezdac~')
p.add_line(osc, gain)
p.add_line(gain, dac)
p.to_svg('example.svg')   # preview
p.save()
```

The SQLite Max-reference database is available lazily as
`from py2max.maxref import MaxRefDB` (kept off the top-level import so
`import py2max` stays light and dependency-free).

## Exceptions

::: py2max.exceptions
    options:
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
