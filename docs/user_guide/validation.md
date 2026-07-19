# Validation and Linting

py2max checks your patch for problems that Max would reject or that indicate a
mistake -- invalid connections, out-of-range ports, overlapping or off-canvas
objects, dangling patchlines, and unknown object classes. There are two layers:

- **Patch linting** runs automatically on `save()` and is available on demand
  via `Patcher.lint()`. It inspects the whole patch and reports structured
  findings.
- **Connection validation** is an opt-in, immediate check at `add_line()` time
  that raises as soon as you make an invalid connection.

## Linting a patch

Call `lint()` for a list of findings, most severe first:

``` python
from py2max import Patcher

p = Patcher()
p.add_line(p.add_textbox('metro 500'), p.add_textbox('cycle~ 440'))

for finding in p.lint():
    print(finding)
```

```
ERROR E-BAD-CONNECTION: cannot connect bang outlet 0 of 'metro' to inlet 0 of 'cycle~' [obj-1:0 -> obj-2:0]
```

(A `metro` sends a *bang*, which an oscillator's signal inlet cannot accept --
Max reports "error connecting outlet ... to ... inlet" for exactly this.)

Each result is a `Finding`:

| Field | Description |
|-------|-------------|
| `code` | short stable identifier, e.g. `E-BAD-CONNECTION` |
| `severity` | `"error"` or `"warning"` |
| `message` | human-readable explanation |
| `obj_id` | the object a finding refers to (or `None`) |
| `line` | `(src_id, outlet, dst_id, inlet)` for connection findings (or `None`) |

### Finding codes

**Errors** -- things Max rejects or that break the patch:

| Code | Meaning |
|------|---------|
| `E-BAD-CONNECTION` | the outlet's message kind is incompatible with the inlet (e.g. a bang into a signal inlet) |
| `E-OUTLET-RANGE` | the outlet index exceeds the object's outlet count |
| `E-INLET-RANGE` | the inlet index exceeds the object's inlet count |
| `E-ORPHAN-LINE` | a patchline references a missing object |
| `E-DUP-ID` | two objects share the same id |

**Warnings** -- suspicious but not fatal:

| Code | Meaning |
|------|---------|
| `W-OVERLAP` | two objects occupy overlapping rectangles |
| `W-OFFCANVAS` | an object extends outside the patcher window |
| `W-UNKNOWN-OBJECT` | the object class is not in the Max reference |

Linting recurses into subpatchers; a finding inside `p sub` is reported with a
path-qualified id (e.g. `sub-box-id/obj-1`).

## Checking on save

`save()` lints automatically. By default it is **non-fatal**: error-severity
findings are logged (via the standard `logging` module) and the file is still
written, so existing workflows are unaffected. Warnings (overlaps, off-canvas,
unknown objects) are left to an explicit `lint()` call to keep saves quiet.

To make errors fatal, create the patcher with `strict=True`:

``` python
from py2max import Patcher, InvalidPatchError

p = Patcher('patch.maxpat', strict=True)
p.add_line(p.add_textbox('metro 500'), p.add_textbox('cycle~ 440'))

try:
    p.save()
except InvalidPatchError as e:
    print(e)   # patch has 1 validation error(s); first: ERROR E-BAD-CONNECTION ...
```

Building the patch correctly (a float number box sets an oscillator's frequency)
saves cleanly under `strict=True`:

``` python
p = Patcher('patch.maxpat', strict=True)
freq = p.add_floatbox()
osc = p.add_textbox('cycle~ 440')
p.add_line(freq, osc)   # float -> frequency inlet: valid
p.save()                # no error
```

## Validating connections as you build

For immediate feedback, enable `validate_connections`. Then `add_line()` raises
`InvalidConnectionError` the moment you make an invalid connection, instead of
waiting for `save()`:

``` python
from py2max import Patcher, InvalidConnectionError

p = Patcher('patch.maxpat', validate_connections=True)
metro = p.add_textbox('metro 500')
osc = p.add_textbox('cycle~ 440')

try:
    p.add_line(metro, osc)          # bang into a signal inlet
except InvalidConnectionError as e:
    print(e)
```

## How the connection check decides

Compatibility is judged from each object's **message vocabulary** -- the methods
it documents in Max's own reference, not a guess. A `cycle~` has no `bang`
method, so a bang into it is rejected; an `adsr~` has an `anything` (wildcard)
method, so a bang -- a legitimate envelope trigger -- is allowed. Port counts are
argument-aware (`limi~ 2` has two inlets/outlets, `select 0 1 2` has four
outlets), and subpatcher ports come from the `inlet`/`outlet` objects inside.

The check is deliberately **conservative**: only clearly-wrong connections fail.
Ambiguous cases, and objects that are not in the Max reference, are allowed --
so validation never rejects a patch that is actually fine. That means it can
miss some genuinely-invalid connections, but it will not produce false alarms.

## From the command line

`py2max validate` lints a saved patch, prints the findings, and exits non-zero
if there are any errors -- useful in a build or CI step:

``` bash
py2max validate patch.maxpat
```

```
  ERROR E-BAD-CONNECTION: cannot connect bang outlet 0 of 'metro' to inlet 0 of 'cycle~' [obj-1:0 -> obj-2:0]
  WARNING W-OVERLAP: objects 'obj-3' and 'obj-4' overlap [obj-3]
1 error(s), 1 warning(s).
```

## Programmatic use

The linter is also importable directly, and the finding codes are exported for
filtering:

``` python
from py2max import lint, Finding
from py2max.lint import ERROR, E_BAD_CONNECTION

findings = lint(patcher)                       # same as patcher.lint()
errors = [f for f in findings if f.severity == ERROR]
bad_connections = [f for f in findings if f.code == E_BAD_CONNECTION]
```
