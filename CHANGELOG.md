# Changelog

## 0.1.1

- Improved core Coverage: 99%

- Added clean script: `./scripts/clean.sh`

- Added coverage script and reporting: `./scripts/coverage.sh`

- Moved `tests` folder from `py2max/py2max/tests` to `py2max/tests`

- Added gradual types to `py2max/core`, no errors with `mypy`

- Added `number_tilde` test

- Fixed `comment` positioning

- Added `pyhola` layout.

- Added `graphviz` layouts.

- Fixed `Adaptagrams` layout.

- Added graph layout comparison and additional layouts.

- Added vertical layout variant.

- Added boolean `tilde` parameter for objects which have a tilde sibling.

- Added preliminary support for `rnbo~` include rnbo codebox

## 0.1

- added a generic `.add` method to `Patcher` objects which inlcude some logic to to figure out to which specialized method to dispatch to. See: `tests/test_add.py` for examples of this.

- Major refactoring after `test_tree_builder` design experiment, so we have now only one simple extendable Box class, and there is round trip conversion between .maxpat files and patchers.

- Added `test_tree_builder.py` which shows that the json tree can be converted to a python object tree which corresponds to it on a one-on-one basis, which itself can be used to generate the json tree for round-trip conversion.

- Added `from_file` classmethod to `Patcher` to populate object from `.maxpat` file.

- Added `coll`, `dict` and `table` objects and tests

- Added some tests which try to use generic layout algorithm in Networkx but the results are quite terrible using builtin algorithms so probably better to try to create something fit-for-purpose.

- Added `gen` subpatcher

- Moved `varname` to optional kwds instead of being an explicit parameter since it's optional and its inclusion when not populated is sometimes problematic.

- Renamed odb to maxclassdb since it only relates to defaults per `maxclass`

- Added smarter textbox which uses odb to improve object creation.

- Added separate test folder

- Added `odb.py` in package with a number of default configs of objects

- Converted to package.

- Added some notes on graph drawing and layout algorithms

- Added comments keyword in box objects + PositionManager for easy documentation

- Added Comments objects

- Refactor: MaxPatch and Patcher objects are now one.

- Initial release
