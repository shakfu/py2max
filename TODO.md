# TODO

## General add

```python

def add(self, value: Any, **kwds):
    """generic add"""

```

## Max Classes

Implement more objects: especially object with state stored in the `.maxpat` file.

Items are checked if they don't need special implementations or have an entry in maxclassdb.

- [ ] bpatcher
- [ ] codebox
- [ ] js
- [ ] funbuff
- [ ] mc objects
- [ ] zl objects

## Other stuff

- Anchor certain objects in expected places in the grid. One way of doing it is to specify x,y ratios as percentages of the grid. So if `x` is 0.10 and the grid width is 500, then x is positioned at 50. The following are typical cases:
  - ezadc~ to top left
  - ezdac~ to bottom left
  - visualization object (scope, etc.) to bottom right

- Parsing of .maxpat files to python objects -- would require rename py2max to py4max to signify py2max and max2py.

- Convert patchlines to references (send/receive)
