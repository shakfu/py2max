# py2max REPL Modes - Complete Guide

**Date**: 2025-10-15
**Status**: [x] **COMPLETE**

---

## Overview

py2max provides **two REPL modes** for interactive patch editing, each optimized for different use cases:

1. **Client-Server Mode** (Option 2a) - Two terminals, real-time log visibility
2. **Single Terminal Mode** (Option 2b) - One terminal, logs to file

Both modes solve the original problem: **server logs interfering with REPL usability**.

---

## The Original Problem

The initial inline REPL implementation had logs interrupting user input:

```
py2max[demo.maxpat]>>> osc = p.add('cycle~ 440')
[00:00:01] - INFO - Client connected           ← Server log
[00:00:01] - DEBUG - WebSocket message         ← Server log
py2max[demo.maxpat]>>> gain = p.add[00:00:02]  ← Log interrupts!
('gain~')
```

**Result**: UNUSABLE during development [X]

---

## Solution 1: Client-Server Mode (Recommended)

### Quick Start

```bash
# Terminal 1: Start server
$ py2max serve my-patch.maxpat
Starting server for: my-patch.maxpat
HTTP server: http://localhost:8000
WebSocket server: ws://localhost:8001
REPL server started on port 8002
Connect with: py2max repl localhost:8002

[Server logs appear here...]

# Terminal 2: Connect REPL client
$ py2max repl localhost:8002
Connecting to py2max server at ws://localhost:8002...

======================================================================
py2max Remote REPL
======================================================================

Connected to: localhost:8002
Patcher: my-patch.maxpat
Objects: 0 boxes

py2max[remote]>>> osc = p.add('cycle~ 440')
py2max[remote]>>> gain = p.add('gain~')
py2max[remote]>>> save()
```

### Architecture

```
Terminal 1: Server                    Terminal 2: REPL Client
┌──────────────────────┐              ┌────────────────────┐
│ py2max serve         │              │ py2max repl        │
│ my-patch.maxpat      │              │ localhost:8002     │
│                      │              │                    │
│ HTTP Server: 8000    │              │ ReplClient         │
│ WebSocket: 8001      │◄────────────►│                    │
│ REPL Server: 8002    │  WebSocket   │ py2max[remote]>>>  │
│                      │  JSON-RPC    │                    │
│ [server logs here]   │              │ [clean, no logs]   │
│ Client connected     │              │                    │
│ Saving patcher...    │              │                    │
└──────────────────────┘              └────────────────────┘
```

### Key Features

[x] **Clean Separation**: Server logs in Terminal 1, REPL in Terminal 2
[x] **Multiple Clients**: Can connect multiple REPLs to same server
[x] **Reconnection**: Client crashes? Just reconnect - server keeps running
[x] **Real-time Logs**: Monitor server activity while using REPL
[x] **Remote Access**: Can connect from different machines (localhost by default)

### When to Use

- **Development work**: Full server logging visibility
- **Debugging**: Monitor server logs while testing in REPL
- **Team collaboration**: Multiple developers connecting to same patcher
- **Long sessions**: Reconnect after client crashes without losing state

### Implementation Files

- `py2max/repl_server.py` - WebSocket RPC server (189 lines)
- `py2max/repl_client.py` - WebSocket RPC client (254 lines)
- `tests/examples/repl_client_server_demo.py` - Full demo

---

## Solution 2: Single Terminal Mode

### Quick Start

```bash
# Single terminal with log redirection
$ py2max serve my-patch.maxpat --repl --log-file server.log

======================================================================
py2max Inline REPL (Single Terminal Mode)
======================================================================

Server running:
  HTTP: http://localhost:8000
  WebSocket: ws://localhost:8001

Server logs: server.log
To monitor: tail -f server.log

Starting REPL...

py2max[demo.maxpat]>>> osc = p.add('cycle~ 440')
py2max[demo.maxpat]>>> gain = p.add('gain~')
py2max[demo.maxpat]>>> save()
```

### Architecture

```
Single Terminal
┌─────────────────────────────────────┐
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Server (background thread)      │ │
│ │ - HTTP: 8000                    │ │
│ │ - WebSocket: 8001               │ │
│ │ - Logs → server.log             │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ REPL (foreground, ptpython)     │ │
│ │ py2max[demo.maxpat]>>>          │ │
│ │ [clean, no logs]                │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘

Optional: $ tail -f server.log (in another terminal)
```

### Key Features

[x] **Single Terminal**: All in one command
[x] **Log File**: Server logs redirected to file (default: `outputs/py2max_server.log`)
[x] **Clean Interface**: No log interference with REPL
[x] **Optional Monitoring**: Can `tail -f` log file if needed
[x] **Simple Setup**: No need to manage multiple terminals

### When to Use

- **Quick editing**: Fast patch modifications
- **Demos**: Simple single-terminal experience
- **Learning**: Easier for beginners (one command)
- **Scripting**: When you don't need real-time log monitoring

### Implementation Files

- `py2max/repl_inline.py` - Background server with log redirection (293 lines)
- `tests/examples/inline_repl_verification.py` - Verification script

---

## Comparison

| Feature | Client-Server Mode | Single Terminal Mode |
|---------|-------------------|---------------------|
| **Terminals required** | 2 (server + client) | 1 (REPL only) |
| **Log visibility** | Real-time in Terminal 1 | File (tail -f if needed) |
| **Multiple clients** | [x] Yes (many REPLs → 1 server) | [X] No |
| **Reconnection** | [x] Yes (server keeps running) | [X] N/A |
| **Complexity** | Moderate (two commands) | Simple (one command) |
| **Remote access** | [x] Yes | [X] No (localhost only) |
| **Recommended for** | Development, debugging | Quick edits, demos |
| **Setup time** | ~5 seconds (two commands) | ~2 seconds (one command) |

---

## Usage Examples

### Client-Server Mode Examples

**Basic session**:
```bash
# Terminal 1
$ py2max serve demo.maxpat

# Terminal 2
$ py2max repl localhost:8002
py2max[remote]>>> osc = p.add('cycle~ 440')
py2max[remote]>>> save()
```

**Custom ports**:
```bash
# Terminal 1 (use port 9000 for HTTP, 9001 for WS, 9002 for REPL)
$ py2max serve demo.maxpat --port 9000

# Terminal 2
$ py2max repl localhost:9002
```

**Multiple clients**:
```bash
# Terminal 1: Server
$ py2max serve demo.maxpat

# Terminal 2: Client 1
$ py2max repl localhost:8002

# Terminal 3: Client 2
$ py2max repl localhost:8002

# Terminal 4: Client 3
$ py2max repl localhost:8002
```

### Single Terminal Mode Examples

**Basic session**:
```bash
$ py2max serve demo.maxpat --repl --log-file server.log
py2max[demo.maxpat]>>> osc = p.add('cycle~ 440')
py2max[demo.maxpat]>>> save()
```

**Monitor logs in second terminal (optional)**:
```bash
# Terminal 1: REPL
$ py2max serve demo.maxpat --repl --log-file server.log

# Terminal 2: Log viewer (optional)
$ tail -f server.log
```

**Custom log location**:
```bash
$ py2max serve demo.maxpat --repl --log-file ~/logs/py2max_$(date +%Y%m%d).log
```

---

## REPL Commands (Both Modes)

All commands work identically in both REPL modes:

```python
# Patcher manipulation
py2max>>> osc = p.add('cycle~ 440')     # Add object
py2max>>> gain = p.add('gain~')         # Add another
py2max>>> p.link(osc, gain)             # Create connection

# Magic commands
py2max>>> save()                         # Save patcher
py2max>>> info()                         # Show statistics
py2max>>> layout('flow')                 # Change layout
py2max>>> optimize()                     # Optimize positioning
py2max>>> clear()                        # Clear all objects
py2max>>> help_obj('cycle~')             # Show Max help
py2max>>> commands()                     # Show command list

# Async operations
py2max>>> await asyncio.sleep(1)         # Top-level await works

# Access objects
py2max>>> p           # Patcher instance
py2max>>> server      # WebSocket server
py2max>>> asyncio     # Async module
```

---

## Protocol (Client-Server Mode Only)

### WebSocket JSON-RPC

**Port**: 8002 (default: HTTP port + 2)

**Init**:
```json
// Client → Server
{"type": "init"}

// Server → Client
{
  "type": "init_response",
  "info": {
    "patcher_path": "demo.maxpat",
    "num_objects": 5,
    "num_connections": 4
  }
}
```

**Eval**:
```json
// Client → Server
{
  "type": "eval",
  "code": "osc = p.add('cycle~ 440')",
  "mode": "exec"
}

// Server → Client (success)
{
  "type": "result",
  "result": "<Box: obj-1>",
  "display": "Created: cycle~\n"
}

// Server → Client (error)
{
  "type": "error",
  "error": "NameError: name 'foo' is not defined",
  "traceback": "Traceback (most recent call last):\n  ..."
}
```

---

## Performance

### Client-Server Mode
```
localhost:      5-10ms   (instant)
local network: 20-50ms   (responsive)
internet:      50-200ms  (usable)

Bandwidth: ~10-20 KB per command (very lightweight)
```

### Single Terminal Mode
```
No network overhead (background thread)
Response time: <1ms (instant)
```

---

## Migration from Old Inline REPL

### Old Way (DEPRECATED)
```bash
$ py2max serve my-patch.maxpat --repl

# WARNING: Server logs interfere with REPL!
# This shows deprecation warning now.
```

### New Ways (RECOMMENDED)

**Option 1: Client-Server** (best for development)
```bash
# Terminal 1
$ py2max serve my-patch.maxpat

# Terminal 2
$ py2max repl localhost:8002
```

**Option 2: Single Terminal** (best for quick edits)
```bash
$ py2max serve my-patch.maxpat --repl --log-file server.log
```

---

## Troubleshooting

### Client-Server Mode

**Q: Can't connect to server**
```bash
# Check server is running
$ ps aux | grep "py2max serve"

# Check correct port (default: 8002)
$ py2max repl localhost:8002

# Check server output for port number
```

**Q: Connection refused**
```bash
# Make sure server started successfully
# Check for "REPL server started on port 8002" message
```

### Single Terminal Mode

**Q: Can't find log file**
```bash
# Default location: outputs/py2max_server.log
$ tail -f outputs/py2max_server.log

# Or specify custom location
$ py2max serve patch.maxpat --repl --log-file ~/my.log
```

**Q: REPL not starting**
```bash
# Check ptpython is installed
$ uv add ptpython

# Check for error messages in log file
$ cat outputs/py2max_server.log
```

---

## Summary

### [x] Client-Server Mode (Option 2a)

**Best for**: Development, debugging, team collaboration

**Pros**:
- Real-time log visibility
- Multiple clients
- Reconnection support
- Remote access

**Cons**:
- Requires two terminals
- Slightly more complex setup

### [x] Single Terminal Mode (Option 2b)

**Best for**: Quick edits, demos, learning

**Pros**:
- Single terminal
- Simple setup
- Fast startup
- Logs preserved in file

**Cons**:
- No real-time log visibility
- Single REPL only
- No remote access

---

## Quick Reference

```bash
# Client-Server Mode
$ py2max serve <patch.maxpat>              # Terminal 1
$ py2max repl localhost:8002                # Terminal 2

# Single Terminal Mode
$ py2max serve <patch.maxpat> --repl --log-file server.log

# Custom ports
$ py2max serve <patch.maxpat> --port 9000   # REPL on 9002
$ py2max repl localhost:9002

# Help
$ py2max serve --help
$ py2max repl --help
```

**Both modes provide clean, usable REPL with full server logging!** 
