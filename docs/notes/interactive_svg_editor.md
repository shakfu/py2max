# Interactive SVG Editor - Design Document

## Vision

Transform the static SVG preview into a live, interactive web-based Max/MSP patch editor that enables:

- **Live REPL Integration**: Real-time visualization as you build patches in Python
- **Interactive Editing**: Drag-and-drop object repositioning, visual connection drawing
- **Layout Experimentation**: Try different layout algorithms interactively
- **Sketch-First Workflow**: Design patches visually, then export to .maxpat
- **Bidirectional Sync**: Changes in browser update Python, changes in Python update browser

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Python REPL                              │
│  >>> from py2max import Patcher                                 │
│  >>> p = Patcher.serve('patch.maxpat', live=True)               │
│  >>> osc = p.add('cycle~ 440')  # Auto-updates browser          │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ WebSocket (bidirectional)
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│              WebSocket Server (Python)                          │
│  - Serves static HTML/JS/CSS                                    │
│  - Manages WebSocket connections                                │
│  - Broadcasts patcher updates                                   │
│  - Receives UI events (drag, connect, add object)               │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ HTTP/WebSocket
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│              Web Browser (Interactive SVG)                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  SVG Canvas                                               │  │
│  │  - Draggable objects                                      │  │
│  │  - Connection drawing                                     │  │
│  │  - Layout controls                                        │  │
│  │  - Object palette                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Python Server (`py2max/server.py`)

```python
from py2max import Patcher
import asyncio
import websockets
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

class PatcherServer:
    """WebSocket server for live patcher editing."""

    def __init__(self, patcher: Patcher, port: int = 8765, http_port: int = 8000):
        self.patcher = patcher
        self.port = port
        self.http_port = http_port
        self.clients = set()

    async def handle_client(self, websocket, path):
        """Handle WebSocket client connection."""
        self.clients.add(websocket)
        try:
            # Send initial patcher state
            await self.send_full_state(websocket)

            # Listen for updates from client
            async for message in websocket:
                await self.handle_message(message)
        finally:
            self.clients.remove(websocket)

    async def handle_message(self, message: str):
        """Handle messages from browser."""
        data = json.loads(message)

        if data['type'] == 'move_box':
            # Update box position in patcher
            box_id = data['box_id']
            x, y = data['position']
            self.patcher.move_box(box_id, x, y)

        elif data['type'] == 'add_object':
            # Add new object
            text = data['text']
            x, y = data['position']
            self.patcher.add_textbox(text, position=(x, y))

        elif data['type'] == 'add_connection':
            # Add patchline
            src_id = data['src_id']
            dst_id = data['dst_id']
            outlet = data.get('outlet', 0)
            inlet = data.get('inlet', 0)
            self.patcher.add_line_by_id(src_id, dst_id, outlet, inlet)

        elif data['type'] == 'apply_layout':
            # Apply layout algorithm
            layout_type = data['layout']
            self.patcher.set_layout(layout_type)
            self.patcher.optimize_layout()

        # Broadcast update to all clients
        await self.broadcast_update()

    async def broadcast_update(self):
        """Broadcast patcher state to all connected clients."""
        if self.clients:
            state = self.get_patcher_state()
            message = json.dumps(state)
            await asyncio.gather(
                *[client.send(message) for client in self.clients]
            )

    def get_patcher_state(self) -> dict:
        """Convert patcher to JSON state for browser."""
        return {
            'type': 'update',
            'boxes': [self.box_to_dict(box) for box in self.patcher._boxes],
            'lines': [self.line_to_dict(line) for line in self.patcher._lines],
        }

    def start(self):
        """Start both HTTP and WebSocket servers."""
        # Start HTTP server in thread
        # Start WebSocket server in asyncio loop
        pass

# Extension to Patcher class
class Patcher:
    def serve(self, port: int = 8765, http_port: int = 8000):
        """Start interactive editing server."""
        server = PatcherServer(self, port, http_port)
        server.start()
        print(f"Interactive editor: http://localhost:{http_port}")
        print(f"WebSocket server: ws://localhost:{port}")
        return server
```

### 2. Web Frontend (`py2max/static/editor.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <title>py2max Interactive Editor</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Monaco, Courier, monospace;
            display: grid;
            grid-template-columns: 250px 1fr;
            grid-template-rows: 60px 1fr 40px;
            height: 100vh;
        }

        #toolbar {
            grid-column: 1 / 3;
            background: #2d2d2d;
            color: #fff;
            padding: 10px;
            display: flex;
            gap: 10px;
            align-items: center;
        }

        #palette {
            background: #f0f0f0;
            padding: 10px;
            overflow-y: auto;
            border-right: 1px solid #ccc;
        }

        #canvas {
            background: #fff;
            overflow: auto;
            position: relative;
        }

        #status {
            grid-column: 1 / 3;
            background: #2d2d2d;
            color: #0f0;
            padding: 10px;
            font-size: 12px;
        }

        .palette-item {
            padding: 8px;
            margin: 5px 0;
            background: white;
            border: 1px solid #ccc;
            cursor: move;
            border-radius: 3px;
        }

        .palette-item:hover {
            background: #e0e0e0;
        }

        svg {
            width: 100%;
            height: 100%;
            cursor: crosshair;
        }

        .box {
            cursor: move;
        }

        .box:hover rect {
            stroke: #4080ff;
            stroke-width: 2;
        }

        .selected rect {
            stroke: #ff8040;
            stroke-width: 2;
        }

        .connection-preview {
            stroke: #ff8040;
            stroke-width: 2;
            stroke-dasharray: 5,5;
        }

        button {
            background: #4080ff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }

        button:hover {
            background: #5090ff;
        }
    </style>
</head>
<body>
    <div id="toolbar">
        <h2>py2max Live Editor</h2>
        <button onclick="applyLayout('grid')">Grid Layout</button>
        <button onclick="applyLayout('flow')">Flow Layout</button>
        <button onclick="applyLayout('matrix')">Matrix Layout</button>
        <button onclick="exportPatch()">Export .maxpat</button>
    </div>

    <div id="palette">
        <h3>Objects</h3>
        <div class="palette-category">
            <h4>Audio</h4>
            <div class="palette-item" draggable="true" data-text="cycle~">cycle~</div>
            <div class="palette-item" draggable="true" data-text="saw~">saw~</div>
            <div class="palette-item" draggable="true" data-text="noise~">noise~</div>
            <div class="palette-item" draggable="true" data-text="gain~">gain~</div>
            <div class="palette-item" draggable="true" data-text="dac~">dac~</div>
            <div class="palette-item" draggable="true" data-text="ezdac~">ezdac~</div>
        </div>
        <div class="palette-category">
            <h4>Control</h4>
            <div class="palette-item" draggable="true" data-text="metro">metro</div>
            <div class="palette-item" draggable="true" data-text="button">button</div>
            <div class="palette-item" draggable="true" data-text="toggle">toggle</div>
            <div class="palette-item" draggable="true" data-text="slider">slider</div>
        </div>
        <div class="palette-category">
            <h4>Math</h4>
            <div class="palette-item" draggable="true" data-text="+">+</div>
            <div class="palette-item" draggable="true" data-text="*">*</div>
            <div class="palette-item" draggable="true" data-text="random">random</div>
        </div>
    </div>

    <div id="canvas">
        <svg id="svg-canvas" viewBox="0 0 1000 800" preserveAspectRatio="xMidYMid meet">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7"
                        refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
                </marker>
            </defs>
            <g id="patchlines"></g>
            <g id="boxes"></g>
        </svg>
    </div>

    <div id="status">
        <span id="connection-status">Connecting...</span>
        <span id="object-count"></span>
    </div>

    <script src="editor.js"></script>
</body>
</html>
```

### 3. Interactive JavaScript (`py2max/static/editor.js`)

```javascript
class PatcherEditor {
    constructor() {
        this.ws = null;
        this.boxes = new Map();
        this.lines = [];
        this.selectedBox = null;
        this.dragging = null;
        this.connectionMode = false;
        this.connectionStart = null;

        this.initWebSocket();
        this.initEventHandlers();
    }

    initWebSocket() {
        this.ws = new WebSocket('ws://localhost:8765');

        this.ws.onopen = () => {
            document.getElementById('connection-status').textContent =
                'Connected [x]';
            document.getElementById('connection-status').style.color = '#0f0';
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleUpdate(data);
        };

        this.ws.onerror = () => {
            document.getElementById('connection-status').textContent =
                'Connection error ';
            document.getElementById('connection-status').style.color = '#f00';
        };
    }

    handleUpdate(data) {
        if (data.type === 'update') {
            this.boxes.clear();
            this.lines = [];

            // Update boxes
            data.boxes.forEach(box => {
                this.boxes.set(box.id, box);
            });

            // Update lines
            this.lines = data.lines;

            // Re-render
            this.render();
        }
    }

    render() {
        const boxesGroup = document.getElementById('boxes');
        const linesGroup = document.getElementById('patchlines');

        // Clear
        boxesGroup.innerHTML = '';
        linesGroup.innerHTML = '';

        // Render patchlines
        this.lines.forEach(line => {
            const srcBox = this.boxes.get(line.src);
            const dstBox = this.boxes.get(line.dst);
            if (srcBox && dstBox) {
                const lineEl = this.createLine(srcBox, dstBox, line);
                linesGroup.appendChild(lineEl);
            }
        });

        // Render boxes
        this.boxes.forEach(box => {
            const boxEl = this.createBox(box);
            boxesGroup.appendChild(boxEl);
        });

        // Update status
        document.getElementById('object-count').textContent =
            `${this.boxes.size} objects, ${this.lines.length} connections`;
    }

    createBox(box) {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('class', 'box');
        g.setAttribute('data-id', box.id);

        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', box.x);
        rect.setAttribute('y', box.y);
        rect.setAttribute('width', box.width);
        rect.setAttribute('height', box.height);
        rect.setAttribute('fill', this.getBoxFill(box));
        rect.setAttribute('stroke', '#333');
        rect.setAttribute('rx', 2);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', box.x + 5);
        text.setAttribute('y', box.y + box.height/2 + 4);
        text.setAttribute('fill', '#000');
        text.setAttribute('font-family', 'Monaco, Courier, monospace');
        text.setAttribute('font-size', 12);
        text.textContent = box.text;

        g.appendChild(rect);
        g.appendChild(text);

        // Make draggable
        this.makeDraggable(g, box);

        return g;
    }

    makeDraggable(element, box) {
        let startX, startY, initialX, initialY;

        element.addEventListener('mousedown', (e) => {
            if (e.shiftKey) {
                // Connection mode
                this.startConnection(box);
            } else {
                // Drag mode
                this.dragging = box;
                startX = e.clientX;
                startY = e.clientY;
                initialX = box.x;
                initialY = box.y;
                element.classList.add('selected');
            }
            e.stopPropagation();
        });

        document.addEventListener('mousemove', (e) => {
            if (this.dragging === box) {
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                box.x = initialX + dx;
                box.y = initialY + dy;
                this.render();
            }
        });

        document.addEventListener('mouseup', () => {
            if (this.dragging === box) {
                this.dragging = null;
                element.classList.remove('selected');

                // Send update to server
                this.ws.send(JSON.stringify({
                    type: 'move_box',
                    box_id: box.id,
                    position: [box.x, box.y]
                }));
            }
        });
    }

    startConnection(box) {
        this.connectionMode = true;
        this.connectionStart = box;
        // Visual feedback...
    }

    getBoxFill(box) {
        if (box.maxclass === 'comment') return '#ffffd0';
        if (box.maxclass === 'message') return '#e0e0e0';
        return '#f0f0f0';
    }
}

// Initialize editor
const editor = new PatcherEditor();

// Layout buttons
function applyLayout(layoutType) {
    editor.ws.send(JSON.stringify({
        type: 'apply_layout',
        layout: layoutType
    }));
}

function exportPatch() {
    editor.ws.send(JSON.stringify({
        type: 'export',
        format: 'maxpat'
    }));
}
```

## Implementation Phases

### Phase 1: Basic Server & Viewer (MVP)

- [x] Static SVG export (already done)
- [ ] Simple HTTP server serving static HTML
- [ ] WebSocket server for live updates
- [ ] Basic real-time viewer (read-only)
- [ ] REPL integration: `patcher.serve()`

### Phase 2: Interactive Editing

- [ ] Drag-and-drop object repositioning
- [ ] Click-to-select objects
- [ ] Bidirectional position sync
- [ ] Save positions back to .maxpat

### Phase 3: Object Creation

- [ ] Object palette sidebar
- [ ] Drag from palette to canvas
- [ ] Double-click to create object
- [ ] Text input for object names

### Phase 4: Connection Drawing

- [ ] Shift+click to start connection
- [ ] Visual connection preview
- [ ] Snap to inlets/outlets
- [ ] Create patchlines in Python

### Phase 5: Layout Algorithms

- [ ] Interactive layout switching
- [ ] JavaScript layout implementations
- [ ] Force-directed layout
- [ ] Grid snapping

### Phase 6: Advanced Features

- [ ] Undo/redo
- [ ] Copy/paste
- [ ] Multi-select
- [ ] Zoom/pan
- [ ] Subpatcher editing

## CLI Integration

```bash
# Start interactive editor
py2max edit my-patch.maxpat

# Start with specific port
py2max edit my-patch.maxpat --port 8080

# Start editor with new patch
py2max edit --new synth.maxpat --template stereo
```

## Python API

```python
from py2max import Patcher

# Method 1: Start server from existing patcher
p = Patcher('synth.maxpat')
p.serve()  # Opens browser automatically

# Method 2: Interactive creation
p = Patcher.serve_new('synth.maxpat')
# Edit in browser, changes reflected in p

# Method 3: REPL-driven with live preview
p = Patcher.serve_live('synth.maxpat')
osc = p.add('cycle~ 440')  # Appears immediately in browser
gain = p.add('gain~')       # Updates in real-time
p.link(osc, gain)          # Connection drawn live
```

## Benefits

1. **Visual Feedback**: See changes immediately as you code
2. **Rapid Prototyping**: Sketch ideas visually, refine in code
3. **Learning Tool**: Understand patch structure interactively
4. **Debugging**: Visualize complex patches during development
5. **Collaboration**: Share live editing sessions
6. **No Max Required**: Complete patch design workflow without Max

## Technical Considerations

### WebSocket vs Server-Sent Events

- **WebSocket**: Bidirectional, better for interactive editing
- **SSE**: Simpler, sufficient for read-only live preview

### State Management

- Python holds authoritative state
- Browser displays current state
- Optimistic updates for responsiveness
- Conflict resolution for concurrent edits

### Performance

- SVG can handle ~100s of objects efficiently
- Virtualization for large patches
- Incremental updates (diff-based)
- Debouncing for drag operations

### Dependencies

- `websockets` or `aiohttp` for async server
- Standard library `http.server` for static files
- No frontend framework required (vanilla JS)
- Optional: D3.js for advanced layouts

## Future Enhancements

1. **Collaborative Editing**: Multiple users editing same patch
2. **Version Control Integration**: Git-aware editing
3. **Plugin System**: Custom object rendering
4. **Mobile Support**: Touch-based editing
5. **Audio Preview**: Play patches directly in browser (Web Audio API)
6. **AI Assistance**: Suggest connections, optimize layouts

## Getting Started

```python
# Install additional dependencies
pip install websockets aiohttp

# Start interactive editor
from py2max import Patcher
p = Patcher('demo.maxpat')
p.serve(port=8000)
# Browser opens to http://localhost:8000
# Edit in real-time!
```

This transforms py2max from a code-generation tool into a complete visual development environment for Max/MSP patches!
