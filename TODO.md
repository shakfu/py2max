# TODO

## Layout

- [ ] Anchor certain objects in expected places in the grid. One way of doing it is to specify x,y ratios as percentages of the grid. So if `x` is 0.10 and the grid width is 500, then x is positioned at 50. The following are typical cases:

  - ezadc~ to top left

  - ezdac~ to bottom left

  - visualization object (scope, etc.) to bottom right, etc.

## Renaming

- [x] add_intbox      -> add_int (as alias)

- [x] add_floatbox    -> add_float (as alias)

## Max Classes

Implement more objects: especially containers / objects with state stored in the `.maxpat` file.

- [x] codebox

- [ ] funbuff

- ...

## Transformations

- Convert patchlines to references (send/receive)

## Development Notes

- convert maxpat to yaml (see `scripts/convert.py`) for ease of reading during dev
- compare using [deepdiff](https://zepworks.com/deepdiff/current/diff.html), see (`scripts/compare.py`)
