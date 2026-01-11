# REPL Solution Comparison for py2max

## Overview

Comparison of three REPL solutions for implementing `py2max serve --repl`:

1. **ptpython** - Enhanced Python REPL built on prompt-toolkit
2. **IPython** - Feature-rich interactive Python shell with magic commands
3. **prompt-toolkit** (raw) - Low-level library for building custom REPLs

**Date**: 2025-10-15
**Context**: Following aioconsole recommendation to use prompt-toolkit-based solutions

---

## Quick Comparison Matrix

| Feature | ptpython | IPython | prompt-toolkit (raw) |
|---------|----------|---------|----------------------|
| **Async Support** | [x] Native via `--asyncio` | [x] Via autoawait | [x] Full control |
| **Embedding** | [x] Simple `embed()` | [x] `IPython.embed()` |  Build from scratch |
| **Magic Commands** | [X] No (use ptipython) | [x] Extensive |  Implement yourself |
| **Syntax Highlighting** | [x] Built-in | [x] Built-in | [x] Via Pygments |
| **Tab Completion** | [x] Built-in | [x] Built-in |  Implement yourself |
| **Command History** | [x] Persistent | [x] Persistent |  Implement yourself |
| **Customization** | [o] Moderate | [o] Moderate | [x] Complete control |
| **Dependencies** | Lightweight | Heavy (many deps) | Minimal (2 deps) |
| **Learning Curve** | Low | Medium | High |
| **Implementation Time** | 1-2 days | 2-3 days | 4-5 days |
| **Weight (PyPI size)** | ~500KB | ~5MB | ~200KB |
| **Documentation** | Good | Excellent | Excellent |

---

## Detailed Analysis

### 1. ptpython (`[*]` RECOMMENDED)

**Project**: <https://github.com/prompt-toolkit/ptpython>
**PyPI**: <https://pypi.org/project/ptpython/>
**Dependencies**: `prompt-toolkit`, `pygments`, `jedi`

#### Strengths

**[x] Perfect Async Support**:

```python
# Embedding ptpython in async context
from ptpython.repl import embed

async def run_repl(patcher, server):
    await embed(
        globals={'p': patcher, 'server': server},
        return_asyncio_coroutine=True,  # Enable async
        patch_stdout=True  # Prevent line interruption
    )
```

**[x] Background Task Support**:

- Coroutines can run while REPL is active
- Perfect for WebSocket server + REPL simultaneously
- Example from ptpython docs shows counter updating while REPL runs

**[x] Rich Interactive Features**:

- Syntax highlighting (Python code)
- Multiline editing with proper indentation
- Autocompletion (via Jedi)
- Vi and Emacs key bindings
- Mouse support
- Persistent history across sessions
- Color schemes

**[x] Simple Embedding**:

```python
from ptpython.repl import embed

# Sync version
embed(globals(), locals())

# Async version
await embed(globals(), locals(), return_asyncio_coroutine=True)
```

**[x] Lightweight**:

- Small footprint (~500KB)
- Only 3 main dependencies
- Fast startup time
- No heavy ecosystem baggage

**[x] Custom Repr Support**:

```python
class Box:
    def __pt_repr__(self):
        # Custom colored representation in ptpython
        return f"<Box: {self.text}>"
```

#### Weaknesses

**[X] No Built-in Magic Commands**:

- ptpython itself doesn't have IPython-style `%magic` commands
- Would need to implement our own (e.g., `%save`, `%info`)
- Alternative: Use `ptipython` (hybrid) for IPython magics

**[o] Limited Customization Compared to Raw**:

- Can't deeply customize the REPL behavior
- Configuration via `config.py` but limited scope
- Less control than building from scratch

**[o] Config Ignored When Embedding**:

- User's `~/.config/ptpython/config.py` not loaded in embedded mode
- Need to configure programmatically

#### Example Implementation

```python
# py2max/repl.py
import asyncio
from ptpython.repl import embed
from prompt_toolkit.styles import Style

async def start_repl(patcher, server):
    """Start ptpython REPL with py2max context."""

    # Create namespace with patcher available
    namespace = {
        'p': patcher,
        'server': server,
        'asyncio': asyncio,
    }

    # Custom configuration
    def configure(repl):
        # Enable Vi mode, set color scheme, etc.
        repl.vi_mode = False
        repl.show_signature = True
        repl.enable_auto_suggest = True

    print("py2max Interactive REPL")
    print(f"Patcher: {patcher.filepath}")
    print(f"Server: http://localhost:{server.port}")
    print("Objects available: p (patcher), server")
    print()

    try:
        await embed(
            globals=namespace,
            return_asyncio_coroutine=True,
            patch_stdout=True,
            configure=configure,
            title="py2max REPL"
        )
    except EOFError:
        print("\nExiting...")
```

#### Verdict for py2max

**Score: 9/10**

**Perfect for py2max because**:

- Native async support (critical for WebSocket server)
- Simple embedding with minimal code
- Professional UX out-of-the-box
- Lightweight dependency footprint
- Background tasks work seamlessly (WebSocket + REPL)

**Trade-offs**:

- Need to implement our own magic commands
- Less flexible than raw prompt-toolkit

**Recommendation**: [x] **Best choice for Phase 1 MVP**

---

### 2. IPython

**Project**: <https://ipython.org/>
**Docs**: <https://ipython.readthedocs.io/>
**Dependencies**: Many (including `traitlets`, `decorator`, `jedi`, `matplotlib-inline`, etc.)

#### Strengths

**[x] Extensive Magic Commands**:

```python
%timeit code          # Time execution
%debug                # Post-mortem debugger
%run script.py        # Run external scripts
%load file.py         # Load file into cell
%history              # Show command history
%who                  # List variables
%edit                 # Open editor
```

- Could reuse many existing magics
- Well-documented system for adding custom magics
- Familiar to Python developers

**[x] Rich Display System**:

- HTML, images, LaTeX rendering
- Could display patch diagrams inline
- Widget support (ipywidgets)
- Integration with Jupyter notebooks

**[x] Excellent Introspection**:

```python
p?        # Show docstring
p??       # Show source code
p.<TAB>   # Completion with docs
```

**[x] Autoawait Support** (IPython 7.0+):

```python
# IPython automatically awaits coroutines
await asyncio.sleep(1)  # Works at top level
result = await some_async_function()
```

**[x] Mature Ecosystem**:

- Huge community
- Extensive documentation
- Many extensions available
- Well-tested in production

#### Weaknesses

**[X] Heavy Dependency Chain**:

```text
IPython requires:
  - traitlets
  - decorator
  - jedi
  - matplotlib-inline
  - prompt-toolkit
  - pygments
  - stack-data
  - pexpect (Unix)
  - pickleshare
  ... and more
```

- ~5MB installation
- Slow startup time
- Many transitive dependencies

**[X] Complex Embedding**:

```python
from IPython import embed

# Sync version
embed()  # Simple

# Async version - more complex
import IPython
from IPython.terminal.embed import InteractiveShellEmbed

# Need to configure event loop integration
ipshell = InteractiveShellEmbed()
ipshell.enable_gui('asyncio')
ipshell()
```

**[X] Autoawait Limitations When Embedded**:

- From IPython docs: "IPython core being asynchronous, the use of `IPython.embed()` will now require a loop to run"
- Default fake coroutine runner may not work well with our WebSocket server
- `%autoawait` feature may not work when embedding

**[o] Overkill for py2max**:

- Most IPython features not needed (matplotlib, widgets, etc.)
- We only need: REPL + async + magic commands
- Brings unnecessary complexity

**[o] Configuration Complexity**:

- Powerful but complex configuration system (traitlets)
- Harder to customize for specific needs

#### Example Implementation

```python
# py2max/repl.py - IPython version
import asyncio
from IPython import embed
from IPython.terminal.prompts import Prompts, Token

class Py2MaxPrompts(Prompts):
    def in_prompt_tokens(self):
        return [
            (Token.Prompt, 'py2max['),
            (Token.PromptNum, self.shell.execution_count),
            (Token.Prompt, ']> '),
        ]

async def start_repl(patcher, server):
    """Start IPython REPL with py2max context."""

    # Configure IPython
    from IPython.terminal.embed import InteractiveShellEmbed

    ipshell = InteractiveShellEmbed(
        banner1="py2max Interactive Shell",
        exit_msg="Goodbye from py2max"
    )

    # Set custom prompt
    ipshell.prompts = Py2MaxPrompts(ipshell)

    # Add custom magics
    from IPython.core.magic import register_line_magic

    @register_line_magic
    def save(line):
        """Save patcher to disk."""
        patcher.save()
        print(f"Saved: {patcher.filepath}")

    # Inject namespace
    ipshell.user_ns.update({
        'p': patcher,
        'server': server,
        'asyncio': asyncio,
    })

    # Run REPL
    ipshell()
```

#### Verdict for py2max

**Score: 6/10**

**Good for py2max if**:

- Users expect IPython features
- Want rich display capabilities
- Need mature magic command system
- Don't mind heavy dependencies

**Problems**:

- Heavy dependency chain (overkill)
- Complex async embedding
- Slower startup
- Autoawait issues when embedded

**Recommendation**: [o] **Possible for Phase 2, but ptpython better**

---

### 3. prompt-toolkit (Raw)

**Project**: <https://github.com/prompt-toolkit/python-prompt-toolkit>
**Docs**: <https://python-prompt-toolkit.readthedocs.io/>
**Dependencies**: Only `pygments` and `wcwidth`

#### Strengths

**[x] Complete Control**:

- Build exactly what you need
- No unnecessary features
- Custom behavior at every level
- Optimize for py2max use case

**[x] Minimal Dependencies**:

```text
Only requires:
  - pygments (syntax highlighting)
  - wcwidth (character width)
```

- Smallest footprint (~200KB)
- Fast startup

**[x] Native Async Support**:

```python
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import PromptSession

async def main():
    session = PromptSession()

    while True:
        with patch_stdout():
            result = await session.prompt_async('>>> ')
        print(f'You said: {result}')
```

**[x] Powerful Features Available**:

- Full-screen applications
- Custom key bindings
- Input validation
- Auto-suggestions
- History management
- Syntax highlighting
- Completions

**[x] Learning Resource**:

- Excellent tutorial for building REPLs
- <https://python-prompt-toolkit.readthedocs.io/en/master/pages/tutorials/repl.html>
- Shows SQLite REPL example

#### Weaknesses

**[X] High Implementation Effort**:

- Must implement everything yourself:
  - Code execution
  - Error handling
  - Multiline editing
  - Completion logic
  - History persistence
  - Syntax highlighting configuration
  - Key bindings
- 4-5 days vs. 1-2 days with ptpython

**[X] Reinventing the Wheel**:

- Python REPL already exists (ptpython)
- Why rebuild what's already built?
- Risk of bugs and edge cases

**[X] More Code to Maintain**:

- Custom REPL = custom bugs
- Need comprehensive tests
- Ongoing maintenance burden

**[o] Steeper Learning Curve**:

- Need to understand prompt-toolkit internals
- More complex than using ptpython
- Documentation is good but requires study

#### Example Implementation Outline

```python
# py2max/repl.py - Raw prompt-toolkit version
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style
from pygments.lexers.python import PythonLexer

class MaxObjectCompleter(Completer):
    """Custom completer for Max objects."""

    def __init__(self, patcher):
        self.patcher = patcher
        # Load Max objects from maxref
        from py2max.maxref import get_available_objects
        self.max_objects = get_available_objects()

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        for obj in self.max_objects:
            if obj.startswith(word):
                yield Completion(obj, start_position=-len(word))

class Py2MaxREPL:
    """Custom REPL for py2max using raw prompt-toolkit."""

    def __init__(self, patcher, server):
        self.patcher = patcher
        self.server = server
        self.namespace = {
            'p': patcher,
            'server': server,
            'asyncio': asyncio,
        }

        # Create session
        self.session = PromptSession(
            history=FileHistory('~/.py2max_history'),
            completer=MaxObjectCompleter(patcher),
            lexer=PygmentsLexer(PythonLexer),
            style=Style.from_dict({
                'prompt': 'bold',
            }),
        )

    async def execute_code(self, code):
        """Execute Python code and return result."""
        try:
            # Handle multiline
            if code.endswith('\\'):
                return None  # Continue

            # Try eval first (for expressions)
            try:
                result = eval(code, self.namespace)
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except SyntaxError:
                # Fall back to exec (for statements)
                exec(code, self.namespace)
                return None

        except Exception as e:
            print(f"Error: {e}")
            return None

    async def run(self):
        """Main REPL loop."""
        print("py2max Interactive REPL (custom)")
        print(f"Patcher: {self.patcher.filepath}")
        print()

        while True:
            try:
                with patch_stdout():
                    code = await self.session.prompt_async(
                        f'py2max[{self.patcher.filepath.name}]> '
                    )

                if not code.strip():
                    continue

                # Execute code
                result = await self.execute_code(code)

                # Show result
                if result is not None:
                    print(result)

                # Auto-sync
                self.patcher.save()
                await self.server.notify_update()

            except EOFError:
                break
            except KeyboardInterrupt:
                continue

async def start_repl(patcher, server):
    """Start custom REPL."""
    repl = Py2MaxREPL(patcher, server)
    await repl.run()
```

**Note**: This is simplified - full implementation needs:

- Proper multiline handling (detect incomplete statements)
- Better error handling and display
- Magic command system
- More sophisticated completion
- Proper async handling for all cases
- Output capturing and formatting
- History search
- Key binding customization
- And much more...

#### Verdict for py2max

**Score: 5/10**

**Good for py2max if**:

- Need highly specialized behavior
- Want minimal dependencies
- Have time for custom development
- Enjoy building infrastructure

**Problems**:

- High implementation effort (4-5 days)
- Reinventing the wheel
- More code to maintain and test
- Not worth it when ptpython exists

**Recommendation**: [X] **Not recommended - use ptpython instead**

---

## Side-by-Side Feature Comparison

### Async Support

| Feature | ptpython | IPython | Raw prompt-toolkit |
|---------|----------|---------|-------------------|
| Top-level await | [x] Native | [x] Autoawait | [x] Custom |
| Background tasks | [x] Perfect | [o] Complex | [x] Perfect |
| Event loop integration | [x] Seamless | [o] Tricky when embedded | [x] Full control |
| Implementation complexity | Low | Medium-High | Medium |

**Winner**: ptpython (seamless async with minimal code)

### Embedding

| Feature | ptpython | IPython | Raw prompt-toolkit |
|---------|----------|---------|-------------------|
| Ease of embedding | [x] Very simple | [o] Moderate | [X] Build yourself |
| Code required | 5-10 lines | 20-30 lines | 100+ lines |
| Namespace injection | [x] Simple dict | [x] Simple dict | [x] Simple dict |
| Configuration | Programmatic | Complex (traitlets) | Full control |

**Winner**: ptpython (simplest embedding API)

### User Experience

| Feature | ptpython | IPython | Raw prompt-toolkit |
|---------|----------|---------|-------------------|
| Syntax highlighting | [x] Python | [x] Python |  Configure yourself |
| Autocompletion | [x] Jedi | [x] Jedi |  Implement yourself |
| Multiline editing | [x] Smart | [x] Smart |  Implement yourself |
| History | [x] Persistent | [x] Persistent |  Implement yourself |
| Vi/Emacs bindings | [x] Both | [x] Both |  Configure yourself |
| Mouse support | [x] Yes | [x] Yes |  Implement yourself |

**Winner**: Tie (ptpython and IPython both excellent, raw = much work)

### Magic Commands

| Feature | ptpython | IPython | Raw prompt-toolkit |
|---------|----------|---------|-------------------|
| Built-in magics | [X] No | [x] ~100+ | [X] No |
| Custom magics |  Implement | [x] Easy system |  Implement |
| Magic syntax | N/A | `%magic` |  Design yourself |

**Winner**: IPython (extensive magic system)

### Dependencies & Size

| Metric | ptpython | IPython | Raw prompt-toolkit |
|--------|----------|---------|-------------------|
| Direct dependencies | 3 | 10+ | 2 |
| Total installed size | ~500KB | ~5MB | ~200KB |
| Startup time | Fast | Slow | Fast |
| Import time | <100ms | ~500ms | <50ms |

**Winner**: Raw prompt-toolkit (smallest), ptpython (good balance)

### Development Effort

| Task | ptpython | IPython | Raw prompt-toolkit |
|------|----------|---------|-------------------|
| Basic REPL | 0.5 day | 1 day | 2-3 days |
| Custom magics | 1 day | 0.5 day | 1-2 days |
| Tab completion | [x] Free | [x] Free | 1 day |
| Full feature set | 1-2 days | 2-3 days | 4-5 days |

**Winner**: ptpython (fastest to working REPL)

---

## Hybrid Options

### Option A: ptipython

**What**: ptpython + IPython combined
**Command**: `ptipython` (separate package)

**Features**:

- ptpython's excellent UX
- IPython's magic commands
- Best of both worlds

**Trade-offs**:

- Heavier dependencies (requires IPython)
- More complex setup
- Two systems to configure

**Verdict**: Good compromise if you need IPython magics

### Option B: ptpython + Custom Magics

**What**: Use ptpython, implement our own magic-like commands

**Approach**:

```python
# Instead of %save, use a function
def save():
    """Magic command replacement."""
    patcher.save()
    print(f"Saved: {patcher.filepath}")

# Make available in namespace
namespace = {'save': save, 'p': patcher}
await embed(globals=namespace)
```

**Pros**:

- Lightweight (no IPython)
- Custom commands tailored for py2max
- Simple implementation

**Cons**:

- Not "real" magic commands
- Different syntax than IPython (`save()` vs `%save`)
- Less discoverable

**Verdict**: `[*]` **Best approach for py2max**

---

## Final Recommendation

### `[*]` Winner: ptpython + Custom Commands

**Rationale**:

1. **Perfect Async Support**: Native `return_asyncio_coroutine=True` works flawlessly with our WebSocket server
2. **Simple Embedding**: 5-10 lines of code vs 20-30 (IPython) or 100+ (raw)
3. **Excellent UX**: Professional REPL experience out-of-the-box
4. **Lightweight**: Only 3 dependencies (~500KB) vs IPython's 10+ dependencies (~5MB)
5. **Fast Implementation**: 1-2 days to working feature vs 4-5 days for raw
6. **Maintainable**: Less custom code = fewer bugs

**Implementation Strategy**:

```python
# Phase 1: Use ptpython directly with custom command functions
from ptpython.repl import embed

async def start_py2max_repl(patcher, server):
    # Custom command functions (magic-like)
    def save():
        """Save patcher to disk."""
        patcher.save()
        print(f"[x] Saved: {patcher.filepath}")

    def info():
        """Show patcher information."""
        print(f"Patcher: {patcher.filepath}")
        print(f"Objects: {len(patcher._boxes)}")
        print(f"Connections: {len(patcher._lines)}")

    def layout(type='grid'):
        """Change layout manager."""
        patcher.set_layout_mgr(type)
        patcher.optimize_layout()
        print(f"[x] Layout changed to: {type}")

    # Namespace with patcher and commands
    namespace = {
        'p': patcher,
        'server': server,
        # Command functions
        'save': save,
        'info': info,
        'layout': layout,
    }

    print("py2max Interactive REPL")
    print(f"Patcher: {patcher.filepath}")
    print()
    print("Available commands:")
    print("  p          - Patcher object")
    print("  save()     - Save patcher")
    print("  info()     - Show patcher info")
    print("  layout(t)  - Change layout")
    print()

    await embed(
        globals=namespace,
        return_asyncio_coroutine=True,
        patch_stdout=True,
        title=f"py2max - {patcher.filepath.name}"
    )
```

**Usage**:

```python
py2max[demo.maxpat]>>> osc = p.add('cycle~ 440')
py2max[demo.maxpat]>>> gain = p.add('gain~')
py2max[demo.maxpat]>>> p.link(osc, gain)
py2max[demo.maxpat]>>> info()
Patcher: demo.maxpat
Objects: 2
Connections: 1
py2max[demo.maxpat]>>> save()
[x] Saved: demo.maxpat
```

---

## Implementation Roadmap

### Phase 1: Basic ptpython REPL (Day 1-2)

**Goal**: Working REPL with auto-sync

**Tasks**:

1. Add ptpython to dependencies
2. Create `py2max/repl.py` with `start_repl()` function
3. Integrate with `cmd_serve()` via `--repl` flag
4. Implement auto-save after commands
5. Implement auto-notify to WebSocket clients
6. Add basic command functions (save, info, layout)
7. Test with example patches

**Deliverable**: `py2max serve --repl patch.maxpat` works

### Phase 2: Enhanced Commands (Day 3)

**Goal**: Rich command set

**Tasks**:

1. Add more command functions:
   - `help(obj)` - Max object help
   - `optimize()` - Layout optimization
   - `clear()` - Clear all objects
   - `clients()` - Show WebSocket clients
2. Add custom `__pt_repr__()` to Box class
3. Improve command output formatting (colors, emojis)
4. Add command documentation to namespace

**Deliverable**: Professional command set

### Phase 3: Tab Completion (Day 4)

**Goal**: Tab complete Max objects

**Tasks**:

1. Create custom completer for Max objects
2. Integrate with ptpython's completion system
3. Add completion for command functions
4. Add completion for patcher methods

**Deliverable**: Tab completion works for Max objects

### Phase 4: Polish (Day 5)

**Goal**: Production-ready

**Tasks**:

1. Custom prompt with patcher name
2. Error handling improvements
3. Documentation (README, examples)
4. Unit tests for REPL
5. Integration tests

**Deliverable**: Ready to ship

---

## Comparison Summary

| Criterion | ptpython | IPython | Raw |
|-----------|----------|---------|-----|
| **Async support** | [*][*][*][*][*] | [*][*][*] | [*][*][*][*][*] |
| **Ease of use** | [*][*][*][*][*] | [*][*][*][*] | [*][*] |
| **Implementation time** | [*][*][*][*][*] (1-2d) | [*][*][*][*] (2-3d) | [*][*] (4-5d) |
| **Dependencies** | [*][*][*][*] (light) | [*][*] (heavy) | [*][*][*][*][*] (minimal) |
| **Features** | [*][*][*][*] | [*][*][*][*][*] | [*][*][*] |
| **Customization** | [*][*][*] | [*][*][*] | [*][*][*][*][*] |
| **Maintenance** | [*][*][*][*][*] | [*][*][*][*] | [*][*] |
| **Overall** | **[*][*][*][*][*]** | **[*][*][*]** | **[*][*]** |

---

## Decision

**Use ptpython** for py2max REPL implementation.

**Justification**:

- Perfect balance of features, simplicity, and implementation time
- Native async support ideal for WebSocket server integration
- Lightweight dependencies appropriate for a library
- Fast time-to-working-feature (1-2 days)
- Excellent out-of-box UX
- Easy to implement custom commands as functions
- Maintainable long-term

**Alternative**: If users strongly request IPython-style magics later, we can always add ptipython support as an option in Phase 3+.

**Next Steps**:

1. Add `ptpython>=3.0.0` to `pyproject.toml` dependencies
2. Implement `py2max/repl.py` following Phase 1 roadmap
3. Add `--repl` flag to `cmd_serve()` in `cli.py`
4. Create example: `examples/repl_quickstart.py`
5. Update `REPL_DEVELOPMENT.md` with chosen solution
