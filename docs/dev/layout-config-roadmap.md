# Roadmap: layout configuration and the `topdown` default

Goals:

1. Layout configuration lives on the layout manager instance, not on `Patcher.__init__`.
2. `layout="topdown"` becomes the default layout.

Each step below is one release. It is releasable on its own and leaves `make test` green with no warnings from py2max's own code. One kind of change per release, so a regression has one cause.

## Current state

Layout keywords on `Patcher.__init__` (`core/patcher.py`):

| Keyword | Read by | When |
|-|-|-|
| `layout` | `set_layout_mgr` | construction |
| `flow_direction` | grid, flow, matrix; `_clear_of_boxes` | as boxes are added |
| `cluster_connected` | grid | `optimize_layout` |
| `signal_order` | grid, horizontal, vertical, topdown | `optimize_layout` |
| `num_dimensions`, `dimension_spacing` | matrix, columnar | as boxes are added and `optimize_layout` |
| `param_placement` | `Patcher._arrange` | `optimize_layout` |
| `auto_layout` | `save_as` | save |

Code outside `Patcher` that reads or writes these as `Patcher` fields:

- `cli.py` (`cmd_new`, `cmd_optimize`) and `transformers.py` (`optimize_layout`, `set_flow_direction`) set `patcher._flow_direction` and rebuild the manager by name.
- `core/abstract.py` declares `_flow_direction`, `_cluster_connected`, `_signal_order`.

Call sites passing the five manager keywords: 102 lines in 24 test files, plus 8 doc files.

## Rules for the end state

- `Patcher(layout="<name>")` builds a manager with that layout's defaults.
- `Patcher(layout_mgr=<instance>)` takes a configured manager. Passing both raises `ValueError`.
- A manager instance belongs to one patcher: it keeps placement counters. Binding one already bound elsewhere raises `ValueError`.
- `optimize_layout()` takes only options that apply to every layout (today: `align_ports`).
- `auto_layout` stays on `Patcher`. It controls saving, not placement.

## Step 1: additive API (no warnings)

- Manager constructors accept `parent=None`; `Patcher` binds the instance.
- `Patcher(layout_mgr=...)`, with the two `ValueError` rules above.
- `align_ports` and `param_placement` become base `LayoutManager` constructor options. `align_ports` already has a class-level default; `topdown` keeps overriding it.
- `GraphLayoutManager`: `algorithm` becomes keyword-only, since `parent` gains a default.
- `cli.py` and `transformers.py` read and write the manager, not `Patcher` fields. A rebuild by name carries the old manager's options over.

Exit: the old keywords still work unchanged; new tests cover `layout_mgr`.

## Step 2: migrate the repository, then deprecate

1. Migrate the 24 test files, 8 doc files, `CLAUDE.md` and the examples to `layout_mgr=`.
2. Add `DeprecationWarning` for `flow_direction`, `cluster_connected`, `signal_order`, `num_dimensions`, `dimension_spacing` and `param_placement`. Combining any of them with `layout_mgr` raises `ValueError`.
3. Add a pytest `filterwarnings` entry that turns the deprecation message into an error, so a missed call site fails `make test`. Match on the message, not the module: with `stacklevel=2` the warning is attributed to the caller.

Keep a single test module that exercises the deprecated keywords on purpose and expects the warning.

Exit: zero deprecation warnings in `make test`; one module tests the deprecated path.

## Step 3: `topdown` becomes the default (done, ahead of step 1)

- `Patcher()` with no `layout` builds `topdown`. Named layouts are unchanged.
- `py2max new --layout` defaults to `topdown`.
- Subpatchers (`Patcher(parent=self)`) default to `topdown` too.
- CHANGELOG upgrade note: placement changes for every patch that names no layout. `layout="horizontal"` restores the old behaviour.
- `auto_layout` stays off by default for every layout, so `save()` never moves boxes unless asked.

Evidence on risk: an earlier trial set the default to `"vertical"`, and the full suite passed unchanged. Few tests assert default positions. The risk is to user scripts, so the release note carries it.

There is no warning before the switch. A warning on every `Patcher()` that names no layout would fire at about 500 call sites in this repository alone.

Exit: CHANGELOG upgrade note; a test pins the default.

## Step 4: remove the deprecated keywords

At least one release after step 2. Remove the six keywords, the `Patcher` fields, and the `abstract.py` declarations.

## Open decisions

1. **Should subpatchers inherit the parent's layout name** rather than take the default? This makes `Patcher(layout="flow")` lay out its subpatchers as flow too.
2. **`configure(**options)` on managers**, so that `optimize_layout(**options)` passes any layout-time option through. Deferred. It needs a rule that rejects options read as boxes are added (`flow_direction`, `pad`), and unknown options must raise.
3. **Version numbers.** The library is pre-1.0, so a minor bump may break. 0.6.0 shipped `align_ports`, `topdown` and step 3. Suggested: steps 1, 2 and 4 as 0.7.0, 0.8.0 and 0.9.0.
