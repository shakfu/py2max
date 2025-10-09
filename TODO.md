# TODO

## General

- [x] Reverse-engineer a `.maxpat` file and produce python code (using py2max)

- [x] Apply patcher to a pipeline of transformations. Each of these is a function which takes a patcher and returns it transformed in some way. For example apply new layout add automatic comments or change font size.

- [x] Add a `py2max preview` command that exports patch layouts to PNG/SVG to enable offline visual validation without Max.

- [ ] Introduce recipe-driven project scaffolding (e.g., `py2max new --from tutorials/basic.yml`) so contributors can spin up teaching or demo patches from structured descriptors.

- [x] Convert maxref files to an sqlite database, would make sense for local caching (retrieval). 

- [ ] Implement nested patchers in the interactive patcher editor

- [ ] Add object groups (can help in layout)

- [ ] Make the colors of the svg similar to Max's colors

- [ ] Run `mypy --strict py2max` and fix all errors.

- [ ] add optional mode where `id==varname` if id is set

- [ ] ensure leaf `box._patcher` is set

- [ ] add combos (pre-combined elements).

- [ ] add groups (grouped elements).

- [ ] add midi inlet / outlets in `add_rnbo`

- [ ] restructure `.add`

- [x] add option to enable semantic ids (e.g. `cycle-1`)

- [ ] add option to convert patchlines to references (send/receive)

- [x] add `find_object_by_id`, `find_object_by_type`

## Layout

- [ ] Anchor certain objects in expected places in the grid. One way of doing it is to specify x,y ratios as percentages of the grid. So if `x` is 0.10 and the grid width is 500, then x is positioned at 50. The following are typical cases:

  - `ezadc~` to top left

  - `ezdac~` to bottom left

  - visualization object (scope, etc.) to bottom right, etc.

## Max Classes

Implement more objects: especially containers / objects with state stored in the `.maxpat` file.

- [x] `codebox`

- [ ] `funbuff`

- ...
