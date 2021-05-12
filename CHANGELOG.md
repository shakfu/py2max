# Changelog

## 0.1

- major refactoring after `test_tree_builder`, so we have now only one simple extendable Box class, and there is round trip conversion between .maxpat files and patchers.

- added `test_tree_builder.py` which shows that the json tree can be converted to a python object tree which corresponds to it on a one-on-one basis, which itself can be used to generate the json tree for round-trip conversion.

- added `from_file` classmethod to `Patcher` to populate object from `.maxpat` file.
- added `coll`, `dict` and `table` objects and tests

- add some tests which try to use generic layout algorithm in Networkx but the results are quite terrible using builtin algorithms so probably better to try to create something fit-for-purpose.
- added `gen` subpatcher
- moved `varname` to optional kwds instead of being an explicit parameter since it's optional and its inclusion when not populated is sometimes problematic.
- renamed odb to maxclassdb since it only relates to defaults per `maxclass`

- smarter textbox which uses odb to improve object creation.
- separate test folder
- added `odb.py` in package with a number of default configs of objects
- converted to package.

- added some notes on graph drawing and layout algorithms
- comments keyword in box objects + PositionManager for easy documentation
- comments objects added
- refactor: MaxPatch and Patcher objects are now one.
- initial release

### objects so far

- [x] abstraction
- [x] subpatcher
- [x] gen~
- [x] dict
- [x] coll
- [x] table
- [x] pv
- [x] pvar
- [x] value
- [x] send
- [x] send~
- [x] receive
- [x] receive~
- [x] multislider
- [x] itable
- [x] poly~
- [x] poly
