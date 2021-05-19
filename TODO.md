# TODO

## Layout

- [ ] Anchor certain objects in expected places in the grid. One way of doing it is to specify x,y ratios as percentages of the grid. So if `x` is 0.10 and the grid width is 500, then x is positioned at 50. The following are typical cases:
  - ezadc~ to top left
  - ezdac~ to bottom left
  - visualization object (scope, etc.) to bottom right, etc.

## Consider Renaming

- [ ] add_textbox     -> add_newobj or add_new()
- [ ] add_intbox      -> add_int
- [ ] add_floatbox    -> add_float

## Max Classes

Implement more objects: especially containers / objects with state stored in the `.maxpat` file.

- [ ] codebox
- [ ] funbuff
- ...

## Tranformations

- Convert patchlines to references (send/receive)
