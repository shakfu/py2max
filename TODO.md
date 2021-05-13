# TODO

## Max Classes

Implement more objects: especially containers / objects with state stored in the `.maxpat` file.

Items are checked if they don't need special implementations or have an entry in maxclassdb.

- [ ] codebox
- [ ] js
- [ ] funbuff
- [ ] mc objects
- [ ] zl objects
- [ ] beap objects

## Other stuff

- Anchor certain objects in expected places in the grid. One way of doing it is to specify x,y ratios as percentages of the grid. So if `x` is 0.10 and the grid width is 500, then x is positioned at 50. The following are typical cases:
  - ezadc~ to top left
  - ezdac~ to bottom left
  - visualization object (scope, etc.) to bottom right

- Convert patchlines to references (send/receive)
