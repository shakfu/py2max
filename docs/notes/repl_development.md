# py2max REPL Development Analysis

## Overview

Analysis of requirements and implementation strategy for adding a `py2max serve` feature with integrated REPL that synchronizes changes bidirectionally with a Max patcher.

**Date**: 2025-10-15
**Status**: Planning Phase

---

## Current State

### Existing Infrastructure ([x] ~70% Complete)

py2max already has substantial infrastructure for this feature:

#### 1. **Server Infrastructure** (`py2max/server.py`)
- WebSocket-based interactive server with bidirectional communication
- Real-time synchronization (Python ↔ Browser)
- Token-based authentication
- Auto-save with debouncing (2-second delay)
- Subpatcher navigation support
- Supported operations:
  - Position updates (drag-and-drop)
  - Object creation/deletion
  - Connection creation/deletion
  - Manual save requests
  - Subpatcher navigation

**Key classes**:
- `InteractiveWebSocketHandler` - WebSocket message handling
- `InteractivePatcherServer` - Server lifecycle management
- `serve_interactive()` - Async server startup function

#### 2. **CLI Integration** (`py2max/cli.py:641-694`)
- `cmd_serve()` function already exists
- Handles existing/new patchers
- Manages WebSocket server lifecycle
- Integrated with argparse
- Support for `--port`, `--no-open`, `--no-save` flags

#### 3. **Example Implementations**
- `live_preview_demo.py:108-156` - REPL mode using `code.interact()`
- `interactive_demo.py` - Demonstrates async updates from Python
- Shows feasibility but requires manual `p.save()` calls

---

## What's Missing for Full REPL Integration

### 1. Enhanced REPL Integration

**Current Limitation**:
- Existing REPL demo uses `code.interact()` which blocks async operations
- Requires manual `p.save()` calls after each operation
- No auto-notification to WebSocket clients

**Requirements**:
- Custom async-aware REPL integration
- Auto-save after each REPL command execution
- Auto-broadcast to WebSocket clients without explicit calls
- Enhanced prompt with patcher context information
- Seamless integration with asyncio event loop

### 2. Max File Watching & Auto-Reload

**Challenge**: Max/MSP doesn't natively auto-reload `.maxpat` files when they change on disk.

**Research Findings**:
- Max's `[filewatch]` object can detect file changes
- JavaScript objects support `autowatch = 1` for auto-reload
- Patchers: **No native auto-reload mechanism exists**

**Current Sync Status**:
| Direction | Status | Notes |
|-----------|--------|-------|
| Python → Browser | [x] Works | Via WebSocket |
| Python → Max | [!] Manual | Requires open/close patch |
| Browser → Python | [x] Works | Via WebSocket |
| Browser → Max | [!] Manual | Requires save + reload |

### 3. REPL Command Extensions

**Current State**: Basic patcher manipulation via standard API

**Desired Features**:
- Magic commands (e.g., `%save`, `%reload`, `%layout`, `%info`, `%help`)
- Tab completion for Max objects (using `maxref` database)
- Inline help for Max objects (integration with `Box.help()`)
- Command history with persistence
- Syntax highlighting for Max object names
- Enhanced error messages with Max object context

---

## Technical Requirements

### Architecture Option 1: AsyncIO-Based REPL ⭐ **RECOMMENDED**

```python
# Conceptual structure
async def serve_with_repl(patcher, port=8000):
    # Start WebSocket server
    server = await patcher.serve(port=port, auto_open=True)

    # Custom async REPL
    repl = AsyncREPL(patcher, server)
    await repl.run()
```

#### Components

**1. AsyncREPL Class**:
- Uses `aioconsole` or `prompt_toolkit` with async support
- Executes commands in async context
- Auto-broadcasts updates to WebSocket clients
- Integrates with patcher state
- Maintains command history

**2. Auto-Sync Wrapper**:
- Wraps patcher methods to auto-save and broadcast
- Example flow:
  ```python
  osc = p.add('cycle~ 440')
  # → Internally: add object → save → notify WebSocket clients
  ```

**3. Enhanced Prompt**:
```
py2max[my-patch.maxpat] >>> osc = p.add('cycle~ 440')
Created: cycle~ (obj-1) at [100.0, 100.0]

py2max[my-patch.maxpat] >>> gain = p.add('gain~')
Created: gain~ (obj-2) at [100.0, 150.0]

py2max[my-patch.maxpat] >>> p.link(osc, gain)
Connected: cycle~[0] → gain~[0]

py2max[my-patch.maxpat] >>> %info
Patcher: my-patch.maxpat
Objects: 2 boxes, 1 connection
Layout: grid (horizontal)
Server: http://localhost:8000 (1 client)
```

**4. Magic Commands**:
- `%save` - Force save to disk
- `%reload` - Reload from disk
- `%layout [type]` - Change layout manager
- `%optimize` - Run layout optimization
- `%info` - Show patcher statistics
- `%help [object]` - Show Max object help
- `%clear` - Clear all objects
- `%undo` - Undo last operation
- `%clients` - Show connected WebSocket clients

#### Pros
- Builds on existing infrastructure
- Reasonable complexity
- Good developer experience
- Natural async integration
- Can add features incrementally

#### Cons
- Requires new dependency (`aioconsole` or `prompt_toolkit`)
- Medium implementation effort
- Max reload still manual

---

### Architecture Option 2: Jupyter-Style Kernel (Advanced)

Implement IPython/Jupyter kernel integration for py2max.

#### Features
- Richer interactive experience
- Cell-based execution model
- Inline visualization of patches (SVG)
- Integration with Jupyter notebooks
- Rich output formatting
- Existing IPython magic commands

#### Implementation
```python
class Py2MaxKernel(IPythonKernel):
    def __init__(self):
        super().__init__()
        self.patcher = None
        self.server = None

    def do_execute(self, code, silent, ...):
        # Execute code
        # Auto-save and notify
        # Return rich output
```

#### Pros
- Excellent developer experience
- Rich ecosystem (widgets, visualization)
- Notebook integration
- Professional-grade REPL

#### Cons
- Heavy dependency (IPython/Jupyter)
- Higher complexity
- Overkill for simple use cases
- Steeper learning curve for implementation

---

### Architecture Option 3: Fork-Based REPL (Simpler but Limited)

Use multiprocessing to run REPL in separate process.

#### Structure
- **Main process**: WebSocket server
- **Child process**: REPL with IPC to main
- **Communication**: Queue/Pipe for state sync

#### Pros
- Simpler implementation
- No async REPL needed
- Familiar `code.interact()` approach

#### Cons
- Less elegant architecture
- Potential synchronization issues
- IPC overhead
- Harder to debug
- Limited integration

---

## Implementation Plan

### Phase 1: Core REPL Integration (MVP)

**Goal**: Basic working REPL with auto-sync

**Tasks**:
1. Create `py2max/repl.py` module
2. Implement `AsyncREPL` class using `aioconsole` or `prompt_toolkit`
3. Add auto-save wrapper for patcher methods
4. Add auto-notification to WebSocket clients
5. Integrate with `cmd_serve()` in `cli.py`
6. Add `--repl` flag to `py2max serve` command
7. Implement basic enhanced prompt with patcher context
8. Write unit tests for REPL core functionality
9. Create example: `examples/repl_demo.py`
10. Document basic usage in README

**Files to create/modify**:
- `py2max/repl.py` (new) - Core REPL implementation
- `py2max/cli.py` (modify) - Add `--repl` flag to `cmd_serve()`
- `examples/repl_demo.py` (new) - Usage demonstration
- `tests/test_repl.py` (new) - REPL unit tests
- `README.md` (modify) - Document REPL feature

**Estimated complexity**: Medium (2-3 days)

**Success criteria**:
- REPL starts with `py2max serve --repl patch.maxpat`
- Commands execute in async context
- Changes auto-save and sync to browser
- Basic prompt shows patcher name
- Graceful shutdown on Ctrl+C

---

### Phase 2: Enhanced Features

**Goal**: Production-ready REPL with power-user features

**Tasks**:
1. Implement magic commands:
   - `%save` - Force save
   - `%layout [type]` - Change layout
   - `%optimize` - Run optimization
   - `%info` - Patcher statistics
   - `%help [object]` - Max object help (using `maxref`)
   - `%clear` - Clear all objects
   - `%clients` - WebSocket client info
2. Add tab completion:
   - Max object names (from `maxref` database)
   - Patcher methods
   - Variable names in scope
3. Implement command history:
   - Persistent history file (`~/.py2max_history`)
   - History search (Ctrl+R)
   - History replay
4. Add syntax highlighting:
   - Max object names
   - Python keywords
   - String literals
5. Enhanced error handling:
   - Catch `InvalidConnectionError`
   - Provide helpful suggestions
   - Context-aware error messages
6. Inline help integration:
   - Use existing `Box.help()` method
   - Show inlet/outlet information
   - Display method signatures
7. Rich output formatting:
   - Color-coded feedback
   - Box/connection creation confirmations
   - Statistics and summaries

**Files to modify**:
- `py2max/repl.py` - Add features
- `py2max/repl_completers.py` (new) - Tab completion logic
- `py2max/repl_magic.py` (new) - Magic command handlers
- `tests/test_repl_magic.py` (new) - Magic command tests
- `docs/repl_reference.md` (new) - REPL command reference

**Estimated complexity**: Medium (2-3 days)

**Success criteria**:
- All magic commands working
- Tab completion for Max objects
- Persistent command history
- Syntax highlighting active
- Help system integrated
- Professional user experience

---

### Phase 3: Max Integration (Optional)

**Goal**: Enable automatic reload in Max/MSP

**Tasks**:
1. Research Max scripting APIs
2. Design helper Max patch with `[filewatch]` object
3. Implement OSC/UDP communication layer
4. Create Python → Max reload trigger
5. Add `--max-reload` flag to enable feature
6. Handle platform-specific differences (macOS/Windows)
7. Test with different Max versions
8. Document setup requirements
9. Provide troubleshooting guide

**Implementation approach**:
```python
# py2max side
class MaxReloadHandler:
    def __init__(self, port=8001):
        self.osc_client = OSCClient('localhost', port)

    async def trigger_reload(self, patch_path):
        # Send OSC message to Max
        await self.osc_client.send('/py2max/reload', [str(patch_path)])

# Max side (pseudocode)
[udpreceive 8001]
  |
[routepass /py2max/reload]
  |
[prepend script reload]
  |
[thispatcher]
```

**Challenges**:
- Max doesn't expose native reload API
- Requires Max-side setup (helper patch)
- Platform-specific behaviors
- Version compatibility issues
- Potential timing/race conditions

**Estimated complexity**: High (4-5 days)

**Success criteria**:
- Max patch auto-reloads on Python changes
- Works on macOS and Windows
- Graceful fallback if Max not running
- Clear setup documentation
- Helper patch template provided

---

## Alternative Approaches

### Alternative 1: Hot-Reload Wrapper

Instead of REPL, implement file-watching for Python scripts:

```bash
py2max watch script.py --serve
```

**How it works**:
- Watches Python script for changes
- Re-executes script on save
- Updates patcher state
- Broadcasts to WebSocket clients

**Use case**:
Development workflow where you edit Python files in your IDE and see live updates in browser.

**Pros**:
- Simpler than REPL
- Familiar development workflow
- Works with any editor
- Easy to implement (`watchdog` library)

**Cons**:
- Less interactive than REPL
- No command history
- No inline evaluation
- Must edit external file

**Implementation**:
```python
# py2max/watcher.py
class ScriptWatcher:
    def __init__(self, script_path, patcher, server):
        self.observer = Observer()
        self.handler = ScriptReloadHandler(script_path, patcher, server)

    async def start(self):
        self.observer.schedule(self.handler, path=script_path.parent)
        self.observer.start()
```

---

### Alternative 2: Hybrid Approach

Combine both REPL and file watching:

```bash
py2max serve patch.maxpat --watch script.py --repl
```

**Features**:
- REPL for quick experimentation
- Script watching for development workflow
- Changes from either source sync to browser
- Best of both worlds

**Pros**:
- Maximum flexibility
- Supports different workflows
- Incremental feature adoption

**Cons**:
- More complex implementation
- Potential state conflicts
- Increased testing surface

---

## Comparison Matrix

| Feature | Current State | REPL Option 1 | REPL Option 2 | Watch Mode | Hybrid |
|---------|--------------|---------------|---------------|------------|--------|
| **Complexity** | N/A | Medium | High | Low | High |
| **Interactive** | N/A | [x] Excellent | [x] Excellent | [X] Limited | [x] Excellent |
| **Auto-sync** | Manual | [x] Auto | [x] Auto | [x] Auto | [x] Auto |
| **Max reload** | Manual | Manual | Manual | Manual | Manual |
| **Dependencies** | websockets | +aioconsole | +ipython | +watchdog | +both |
| **Dev experience** | N/A | Good | Excellent | Fair | Excellent |
| **Learning curve** | N/A | Low | Medium | Low | Medium |
| **Implementation time** | N/A | 2-3 days | 5-7 days | 1-2 days | 4-5 days |

---

## Recommendations

### 1. Start with Option 1 (AsyncIO-Based REPL) ⭐

**Rationale**:
- Builds on existing infrastructure (WebSocket server)
- Reasonable complexity with good ROI
- Natural fit for async architecture
- Can add watch mode later (Phase 4)
- Good developer experience without heavy dependencies

### 2. Key Implementation Details

**Primary file**: `py2max/repl.py`

**Core components**:
```python
class AsyncREPL:
    """Async-aware REPL for py2max with auto-sync."""

    def __init__(self, patcher, server):
        self.patcher = patcher
        self.server = server
        self.history = []
        self.completer = MaxObjectCompleter()

    async def run(self):
        """Main REPL loop."""
        while True:
            try:
                code = await self.get_input()
                result = await self.execute(code)
                await self.display_result(result)
                await self.auto_sync()
            except (EOFError, KeyboardInterrupt):
                break

    async def auto_sync(self):
        """Auto-save and notify WebSocket clients."""
        self.patcher.save()
        await self.server.notify_update()
```

### 3. CLI Integration

**Minimal changes to `cli.py`**:

```python
def cmd_serve(args: argparse.Namespace) -> int:
    """Start interactive WebSocket server for a patcher."""
    import asyncio

    # ... existing setup code ...

    async def run_server():
        server = await patcher.serve(port=args.port, auto_open=not args.no_open)

        if args.repl:  # NEW
            from .repl import AsyncREPL
            repl = AsyncREPL(patcher, server)
            await repl.run()
        else:
            # Existing: keep running until Ctrl+C
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass

        await server.stop()

    asyncio.run(run_server())
```

**Add to argparse**:
```python
serve_parser.add_argument(
    "--repl",
    action="store_true",
    help="Start interactive REPL for live patch editing"
)
```

### 4. Documentation Needs

**Essential documentation**:
1. **README.md section**: "Interactive REPL Mode"
2. **REPL_REFERENCE.md**: Complete command reference
3. **Examples**:
   - `examples/repl_quickstart.py`
   - `examples/repl_advanced.py`
4. **Known limitations**: Max auto-reload caveat
5. **Workflow guide**: When to use REPL vs. script vs. browser

---

## Critical Architectural Decision: Max Auto-Reload

The biggest challenge is Max/MSP's lack of native auto-reload for `.maxpat` files.

### Options Analysis

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **A. Document manual reload** | Simple, no code changes | User must reload manually | [x] Phase 1 |
| **B. OSC/UDP trigger** | Automated reload possible | Requires Max helper patch | ⭐ Phase 3 |
| **C. AppleScript/AutoHotkey** | Platform automation | Fragile, platform-specific | [X] Avoid |
| **D. Browser-only workflow** | Already works perfectly | Can't test in Max directly | [x] Recommend |

### Recommended Strategy

**Phase 1 & 2**:
- Focus on **A + D**: Document manual reload + emphasize browser workflow
- Browser viewer provides instant feedback
- Users can test in Max periodically

**Phase 3** (if user demand exists):
- Add **B**: OSC/UDP trigger with optional helper patch
- Provide template Max patch with `[filewatch]` → `[udpreceive]` → reload logic
- Make it opt-in with `--max-reload` flag

### User Workflow (Phase 1)

```bash
# Terminal 1: Start REPL server
$ py2max serve my-patch.maxpat --repl
Starting interactive server...
Browser opened at http://localhost:8000
py2max[my-patch.maxpat] >>>

# Browser: Watch live updates

# Terminal 1: Edit patch interactively
py2max[my-patch.maxpat] >>> osc = p.add('cycle~ 440')
Created: cycle~ at [100.0, 100.0]
py2max[my-patch.maxpat] >>> gain = p.add('gain~')
Created: gain~ at [100.0, 150.0]
py2max[my-patch.maxpat] >>> p.link(osc, gain)
Connected: cycle~[0] → gain~[0]

# Browser: See updates in real-time [x]

# Max: Open my-patch.maxpat to test audio
# (will need to reload if you make more changes)
```

---

## Dependencies

### Required Dependencies

**Already in project**:
- `websockets>=12.0` [x]

**New dependencies** (Phase 1):
- `aioconsole>=0.6.0` OR `prompt_toolkit>=3.0.0`
  - Recommendation: `aioconsole` (lighter, simpler)

**New dependencies** (Phase 2):
- `pygments>=2.0.0` (syntax highlighting)

**New dependencies** (Alternative: Watch Mode):
- `watchdog>=3.0.0` (file watching)

### Optional Dependencies (Phase 3)

**For Max integration**:
- `python-osc>=1.8.0` (OSC communication)

---

## Testing Strategy

### Unit Tests

**Core REPL tests** (`tests/test_repl.py`):
- REPL initialization
- Command execution
- Auto-sync behavior
- Error handling
- Graceful shutdown

**Magic command tests** (`tests/test_repl_magic.py`):
- Each magic command
- Parameter validation
- Error cases

**Integration tests** (`tests/test_repl_integration.py`):
- REPL + WebSocket server
- Browser communication
- State synchronization

### Manual Testing Checklist

- [ ] REPL starts with `py2max serve --repl patch.maxpat`
- [ ] Create new patch if doesn't exist
- [ ] Load existing patch correctly
- [ ] Commands execute without errors
- [ ] Auto-save after each command
- [ ] Browser updates in real-time
- [ ] Magic commands work
- [ ] Tab completion works
- [ ] Command history persists
- [ ] Syntax highlighting displays
- [ ] Ctrl+C exits gracefully
- [ ] Error messages are helpful
- [ ] Works with subpatchers
- [ ] Multiple browser clients stay in sync

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AsyncIO complexity | Medium | Medium | Use proven libraries (aioconsole) |
| State sync issues | Low | High | Comprehensive tests, atomic operations |
| Max reload limitation | Certain | Medium | Clear documentation, browser workflow |
| Performance with large patches | Medium | Low | Lazy loading, optimize serialization |
| WebSocket connection stability | Low | Medium | Reconnection logic, error handling |

### User Experience Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Confusion about Max reload | High | Low | Clear documentation, warnings |
| REPL learning curve | Medium | Low | Good examples, inline help |
| Dependency installation issues | Low | Medium | Clear requirements.txt, error messages |

---

## Success Metrics

### Phase 1 (MVP)
- [ ] REPL starts successfully
- [ ] Basic commands work
- [ ] Auto-sync to browser
- [ ] 90%+ test coverage
- [ ] Zero critical bugs

### Phase 2 (Enhanced)
- [ ] All magic commands implemented
- [ ] Tab completion works
- [ ] Command history persists
- [ ] Positive user feedback
- [ ] Documentation complete

### Phase 3 (Max Integration)
- [ ] Max reload trigger works
- [ ] Cross-platform support
- [ ] Setup documentation clear
- [ ] Optional helper patch provided

---

## Timeline Estimate

| Phase | Duration | Dependencies | Risk Level |
|-------|----------|--------------|------------|
| Phase 1: MVP | 2-3 days | aioconsole | Low |
| Phase 2: Enhanced | 2-3 days | Phase 1 | Low |
| Phase 3: Max Integration | 4-5 days | Phase 1 | Medium-High |
| **Total (Phase 1+2)** | **4-6 days** | - | **Low** |
| **Total (All phases)** | **8-11 days** | - | **Medium** |

---

## Conclusion

The `py2max serve --repl` feature is **highly feasible** with approximately **70% of infrastructure already in place**.

### Key Takeaways

[x] **Strong foundation**:
- WebSocket server with bidirectional sync
- Browser-based editor
- CLI integration
- Existing examples

[!] **Moderate implementation effort**:
- AsyncIO-based REPL (~2-3 days)
- Magic commands and enhancements (~2-3 days)
- Total MVP + Enhanced: ~4-6 days

[X] **Known limitation**:
- Max doesn't auto-reload `.maxpat` files
- Workaround: Use browser for live feedback
- Optional: OSC trigger in Phase 3

### Recommended Action

**Implement Phase 1 + 2** (MVP + Enhanced Features):
- Use AsyncIO-based REPL (Option 1)
- `aioconsole` for async input
- Focus on browser workflow
- Defer Max integration to Phase 3
- Target timeline: **4-6 days**

This provides excellent ROI with reasonable effort, building naturally on existing infrastructure while delivering a professional developer experience.
