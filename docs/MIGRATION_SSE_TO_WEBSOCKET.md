# Migration Guide: SSE Server Removed

**Date**: 2025-10-09
**Version**: 0.1.3+

## Summary of Changes

The legacy SSE (Server-Sent Events) server has been removed from py2max. The WebSocket-based interactive server is now the **only** server implementation, accessed via the `serve` command.

---

## What Changed

### Before (v0.1.2 and earlier)

**Two separate servers:**

1. **SSE Server** (read-only)
   - Command: `py2max serve`
   - Method: `patcher.serve()`
   - Direction: Python → Browser only
   - No dependencies

2. **WebSocket Server** (interactive)
   - Command: `py2max serve-interactive`
   - Method: `patcher.serve_interactive()`
   - Direction: Python ↔ Browser
   - Required: `websockets` package

### After (v0.1.3+)

**One unified server:**

- **WebSocket Server** (interactive)
  - Command: `py2max serve`
  - Method: `patcher.serve()`
  - Direction: Python ↔ Browser
  - Required: `websockets` package (now in dependencies)

---

## Breaking Changes

### 1. CLI Command Changes

#### Before
```bash
# Read-only preview
py2max serve patch.maxpat

# Interactive editing
py2max serve-interactive patch.maxpat
```

#### After
```bash
# Single command - always interactive
py2max serve patch.maxpat
```

**Migration**: Replace `serve-interactive` with `serve`

### 2. Python API Changes

#### Before
```python
# SSE server (removed)
server = patcher.serve()

# WebSocket server
server = await patcher.serve_interactive()
```

#### After
```python
# WebSocket server only
server = await patcher.serve()
```

**Migration**:
- Replace `serve_interactive()` with `serve()`
- Ensure you're using `await` (async required)

### 3. Dependencies

#### Before
```toml
dependencies = []  # websockets optional
```

#### After
```toml
dependencies = [
    "websockets>=12.0",  # Now required
]
```

**Migration**: Install websockets
```bash
pip install websockets
```

---

## Migration Steps

### For CLI Users

**Old code:**
```bash
py2max serve-interactive my-patch.maxpat
```

**New code:**
```bash
py2max serve my-patch.maxpat
```

### For Python API Users

**Old code:**
```python
import asyncio
from py2max import Patcher

async def main():
    p = Patcher('demo.maxpat')
    server = await p.serve_interactive(port=8000)
    # ... code ...
    await server.shutdown()

asyncio.run(main())
```

**New code:**
```python
import asyncio
from py2max import Patcher

async def main():
    p = Patcher('demo.maxpat')
    server = await p.serve(port=8000)  # ← Changed
    # ... code ...
    await server.shutdown()

asyncio.run(main())
```

### For Library Developers

If your code referenced the old SSE server:

**Old code:**
```python
from py2max.server import serve_patcher, PatcherServer  # ← Removed
```

**New code:**
```python
from py2max.websocket_server import serve_interactive, InteractivePatcherServer
```

---

## Rationale

### Why Remove SSE Server?

1. **Redundancy**: Two servers for same purpose
2. **User confusion**: Which one to use?
3. **Feature parity**: WebSocket does everything SSE does + more
4. **Maintenance burden**: Two codebases to maintain
5. **Better UX**: Interactive editing is superior

### Why WebSocket Won?

| Feature | SSE (removed) | WebSocket (kept) |
|---------|---------------|------------------|
| Direction | Python → Browser | Python ↔ Browser |
| Drag objects | ❌ No | ✅ Yes |
| Draw connections | ❌ No | ✅ Yes |
| Auto-save | ❌ No | ✅ Yes |
| Live updates | ✅ Yes | ✅ Yes |
| Dependencies | None | websockets |

WebSocket provides strictly more functionality.

---

## FAQ

### Q: Why was SSE removed?

**A**: WebSocket does everything SSE did, plus interactive editing. No reason to maintain two servers.

### Q: I don't want to install websockets

**A**: websockets is now a core dependency (lightweight, pure Python). If you truly can't install it, stay on v0.1.2.

### Q: My CI/CD uses `py2max serve`

**A**: It still works! Just ensure `websockets` is installed:
```yaml
- run: pip install websockets
- run: py2max serve patch.maxpat --no-open
```

### Q: Can I still use read-only mode?

**A**: Yes, just don't edit in the browser. The server doesn't enforce editing.

### Q: Will old patches still work?

**A**: Yes! This only affects the server, not patch files.

### Q: What if I was using serve() sync method?

**A**: That method was removed. You must now use async:
```python
# Old (removed)
server = patcher.serve()  # sync

# New (required)
server = await patcher.serve()  # async
```

---

## Upgrade Checklist

- [ ] Install websockets: `pip install websockets`
- [ ] Replace `serve-interactive` with `serve` in CLI commands
- [ ] Replace `serve_interactive()` with `serve()` in Python code
- [ ] Ensure async/await is used (not sync)
- [ ] Remove any imports from `py2max.server` (module removed)
- [ ] Update documentation/scripts referencing old commands
- [ ] Test server functionality
- [ ] Update CI/CD pipelines

---

## Timeline

- **v0.1.2 and earlier**: Both servers available
- **v0.1.3**: SSE server removed, WebSocket unified as `serve`
- **Future**: Additional features for WebSocket server

---

## Getting Help

If you encounter issues during migration:

1. Check this migration guide
2. Review updated documentation in README.md
3. Open an issue on GitHub
4. Check examples in `tests/test_websocket.py`

---

## Appendix: Removed Files

The following files were removed:

- `py2max/server.py` - SSE server implementation
- `tests/test_server.py` - SSE server tests
- `docs/SERVER_GUIDE.md` - Old server comparison docs
- `docs/SERVER_COMMANDS.md` - Old command reference

The following was moved:

- `get_patcher_state_json()` - Moved from `server.py` to `websocket_server.py`

---

## Appendix: Feature Comparison

### What You're Not Losing

Everything the SSE server could do, WebSocket can do:

✅ Live preview in browser
✅ Real-time updates from Python
✅ SVG rendering
✅ Works with REPL
✅ Custom ports
✅ Auto-open browser

### What You're Gaining

New features with WebSocket only:

✅ Drag-and-drop repositioning
✅ Visual connection drawing
✅ Bidirectional sync
✅ Auto-save changes
✅ Browser-based editing

---

## Complete Example: Before & After

### Before (v0.1.2)

```python
from py2max import Patcher
import time

# SSE server (sync)
p = Patcher('demo.maxpat')
server = p.serve(port=8000, auto_open=True)

# Add objects
osc = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
p.add_line(osc, gain)
p.save()  # Browser updates

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    server.stop()
```

### After (v0.1.3)

```python
from py2max import Patcher
import asyncio

# WebSocket server (async)
async def main():
    p = Patcher('demo.maxpat')
    server = await p.serve(port=8000, auto_open=True)

    # Add objects
    osc = p.add_textbox('cycle~ 440')
    gain = p.add_textbox('gain~')
    p.add_line(osc, gain)
    p.save()  # Browser updates

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.shutdown()

asyncio.run(main())
```

**Key differences:**
1. `async def main()` - Now async
2. `await p.serve()` - Await required
3. `await asyncio.sleep(1)` - Async sleep
4. `await server.shutdown()` - Async shutdown
5. `asyncio.run(main())` - Run async code

---

This migration simplifies py2max while providing better functionality. The WebSocket server is more powerful and offers a superior development experience.
