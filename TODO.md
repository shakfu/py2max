# TODO

## General

- [ ] add combos (pre-combined elements).

- [ ] add midi inlet / outlets in `add_rnbo`

- [ ] restructure `.add`

- [ ] add option to enable semantic ids (e.g. `cycle-1`)

- [ ] add option to convert patchlines to references (send/receive)

- [ ] add `find_object_by_id`, `find_object_by_type`

## Layout

- [ ] Anchor certain objects in expected places in the grid. One way of doing it is to specify x,y ratios as percentages of the grid. So if `x` is 0.10 and the grid width is 500, then x is positioned at 50. The following are typical cases:

  - `ezadc~` to top left

  -`ezdac~` to bottom left

  - visualization object (scope, etc.) to bottom right, etc.

## Max Classes

Implement more objects: especially containers / objects with state stored in the `.maxpat` file.

- [x] `codebox`

- [ ] `funbuff`

- ...
