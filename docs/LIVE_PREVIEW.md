## Live Preview - Real-Time Patch Visualization

py2max now includes a live preview server that provides real-time visualization of Max patches as you build them in Python. Using Server-Sent Events (SSE), the browser automatically updates whenever you modify your patcher.

### Features

- **Pure Python stdlib** - No external dependencies
- **Real-time updates** - Browser updates as you code
- **Automatic browser opening** - Starts and opens browser automatically
- **SSE-based** - Uses Server-Sent Events for one-way communication
- **Clean SVG rendering** - Same high-quality visualization as static export

### Quick Start

#### Python API

```python
from py2max import Patcher

# Create patcher and start live server
p = Patcher('synth.maxpat')
p.serve()  # Opens browser automatically

# Add objects - browser updates in real-time!
osc = p.add_textbox('cycle~ 440')
p.save()  # Triggers update

gain = p.add_textbox('gain~')
p.save()

p.add_line(osc, gain)
p.save()
```

#### CLI

```bash
# Start server for existing patch
py2max serve my-patch.maxpat

# Use custom port
py2max serve my-patch.maxpat --port 8080

# Don't auto-open browser
py2max serve my-patch.maxpat --no-open
```

### How It Works

```
┌──────────────┐                    ┌──────────────┐
│ Python REPL  │                    │   Browser    │
│              │                    │              │
│  p.add(...)  │                    │  SVG Canvas  │
│  p.save()───────SSE Events────────▶  (updates)   │
│              │                    │              │
└──────────────┘                    └──────────────┘
        │
        │
    HTTP Server
   (port 8000)
```

**Server-Sent Events (SSE):**
- One-way communication: Python → Browser
- Automatic reconnection on disconnect
- Keepalive mechanism
- Pure stdlib implementation

### Usage Examples

#### Example 1: Basic Live Development

```python
from py2max import Patcher

# Start live server
p = Patcher('demo.maxpat', layout='grid')
server = p.serve(port=8000)

# Build patch - watch browser update!
metro = p.add_textbox('metro 500')
p.save()

osc = p.add_textbox('cycle~ 440')
p.save()

p.add_line(metro, osc)
p.save()

# Optimize layout
p.optimize_layout()
p.save()

# Keep server running
input("Press Enter to stop server...")
server.stop()
```

#### Example 2: Interactive REPL

```python
from py2max import Patcher

# Start server
p = Patcher('interactive.maxpat')
p.serve()

# Now you can interactively add objects:
>>> osc1 = p.add_textbox('cycle~ 440')
>>> p.save()  # Browser updates!

>>> osc2 = p.add_textbox('saw~ 220')
>>> p.save()

>>> mix = p.add_textbox('+~')
>>> p.add_line(osc1, mix)
>>> p.add_line(osc2, mix, inlet=1)
>>> p.save()
```

#### Example 3: Automated Demo

```python
from py2max import Patcher
import time

p = Patcher('automated_demo.maxpat')
p.serve()

# Add objects with delays
objects = [
    'metro 1000',
    'random 127',
    'mtof',
    'cycle~',
    'gain~ 0.3',
    'ezdac~'
]

boxes = []
for obj_text in objects:
    print(f"Adding {obj_text}...")
    box = p.add_textbox(obj_text)
    boxes.append(box)
    p.save()
    time.sleep(1)

# Connect sequentially
for i in range(len(boxes) - 1):
    print(f"Connecting {i} -> {i+1}...")
    p.add_line(boxes[i], boxes[i+1])
    p.save()
    time.sleep(1)

print("Done! Server running...")
```

### Server API

#### Patcher.serve()

```python
def serve(self, port: int = 8000, auto_open: bool = True) -> PatcherServer
```

**Args:**
- `port` (int): HTTP server port (default: 8000)
- `auto_open` (bool): Auto-open browser (default: True)

**Returns:**
- `PatcherServer`: Server instance

**Example:**
```python
server = p.serve(port=8080, auto_open=False)
```

#### PatcherServer Methods

**`server.notify_update()`**
Manually trigger an update to all connected clients.

```python
p = Patcher('patch.maxpat')
server = p.serve()

# Modify patcher without calling save()
p.add_textbox('cycle~')
p.add_textbox('gain~')

# Manual notification
server.notify_update()
```

**`server.stop()`**
Stop the server.

```python
server.stop()
```

### Architecture

#### Server Components

1. **SSEHandler** - HTTP request handler with SSE support
   - Serves static HTML/JS files
   - Manages SSE connections
   - Broadcasts updates to clients

2. **PatcherServer** - Server lifecycle manager
   - Starts HTTP server in background thread
   - Manages client connections
   - Coordinates updates

3. **Static Files**
   - `index.html` - Live preview page
   - `live-preview.js` - Client-side rendering

#### Update Flow

```python
# User adds object
osc = p.add_textbox('cycle~ 440')

# User saves
p.save()  # ← Triggers notification

# Server broadcasts to all clients
server.notify_update()

# Browser receives SSE event
# JavaScript renders updated SVG
```

### Browser Interface

The live preview browser interface shows:

- **Real-time SVG rendering** of the patch
- **Connection status** indicator (Connected/Disconnected)
- **Object count** and connection count
- **Automatic reconnection** on disconnect

**Keyboard shortcuts:**
- `Ctrl+R` - Refresh view
- `F11` - Fullscreen

### Advanced Usage

#### Multiple Patchers

```python
# Serve multiple patchers on different ports
p1 = Patcher('synth.maxpat')
s1 = p1.serve(port=8000)

p2 = Patcher('effects.maxpat')
s2 = p2.serve(port=8001)

# Both update independently
p1.add_textbox('cycle~')
p1.save()  # Updates port 8000

p2.add_textbox('reverb~')
p2.save()  # Updates port 8001
```

#### Custom Update Frequency

```python
# Batch updates for performance
p = Patcher('patch.maxpat')
server = p.serve()

# Add many objects without triggering updates
for i in range(100):
    p.add_textbox(f'object{i}')

# Single update at the end
server.notify_update()
```

#### Integration with Jupyter Notebooks

```python
# In Jupyter notebook
from py2max import Patcher
from IPython.display import IFrame

p = Patcher('notebook_demo.maxpat')
server = p.serve(port=8765, auto_open=False)

# Display in iframe
IFrame('http://localhost:8765', width=800, height=600)

# Modify and see updates
p.add_textbox('cycle~ 440')
p.save()
```

### Troubleshooting

#### Port Already in Use

```python
# Use a different port
server = p.serve(port=8080)
```

#### Browser Doesn't Open

```python
# Manually open the URL
server = p.serve(auto_open=False)
print(f"Open: http://localhost:8000")
```

#### Updates Not Showing

Make sure to call `p.save()` after modifications:

```python
p.add_textbox('cycle~')
p.save()  # ← Required for update!
```

Or manually notify:

```python
p.add_textbox('cycle~')
server.notify_update()
```

#### Connection Lost

The browser will automatically attempt to reconnect every 3 seconds. If reconnection fails:

1. Check that the server is still running
2. Check console for errors (`Ctrl+Shift+I` in browser)
3. Restart the server

### Performance Considerations

- **Update Frequency**: Call `save()` after batches of changes, not after each object
- **Large Patches**: Works efficiently with ~100s of objects
- **Multiple Clients**: Each browser connection consumes minimal resources
- **Memory**: Server runs in background thread with minimal overhead

### Limitations

- **One-way Communication**: SSE provides Python → Browser updates only
- **No Interactive Editing**: Browser is read-only (view-only mode)
- **Single Machine**: Server binds to localhost only

For bidirectional communication and interactive editing, see the WebSocket version (Python 3.11+).

### Next Steps

- **WebSocket Version**: Full bidirectional communication (coming soon)
- **Interactive Editing**: Drag-drop, connection drawing (coming soon)
- **Collaborative Editing**: Multiple users (future)

### See Also

- [SVG Preview Documentation](SVG_PREVIEW.md)
- [Interactive Editor Design](INTERACTIVE_SVG_EDITOR.md)
- [Python API Reference](../README.md#python-api-examples)
