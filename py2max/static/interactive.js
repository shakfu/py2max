/**
 * py2max Interactive Editor - Client-side JavaScript
 * Uses WebSocket for bidirectional real-time communication
 */

class InteractiveEditor {
    constructor() {
        this.boxes = new Map();
        this.lines = [];
        this.ws = null;
        this.svgNS = 'http://www.w3.org/2000/svg';

        // Interaction state
        this.selectedBox = null;
        this.dragging = false;
        this.dragOffset = { x: 0, y: 0 };
        this.connectionMode = false;
        this.connectionStart = null;

        this.initializeWebSocket();
        this.initializeSVG();
        this.initializeControls();
    }

    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // WebSocket runs on port + 1
        const wsPort = parseInt(window.location.port) + 1;
        const wsUrl = `${protocol}//${window.location.hostname}:${wsPort}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.updateStatus('Connected', 'connected');
            console.log('WebSocket connection opened');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleUpdate(data);
        };

        this.ws.onerror = (error) => {
            this.updateStatus('Error', 'disconnected');
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            this.updateStatus('Disconnected', 'disconnected');
            console.log('WebSocket connection closed');

            // Attempt to reconnect
            setTimeout(() => {
                this.updateStatus('Reconnecting...', 'disconnected');
                this.initializeWebSocket();
            }, 3000);
        };
    }

    initializeSVG() {
        const canvas = document.getElementById('canvas');

        // Create SVG element
        this.svg = document.createElementNS(this.svgNS, 'svg');
        this.svg.setAttribute('width', '100%');
        this.svg.setAttribute('height', '100%');
        this.svg.setAttribute('viewBox', '0 0 1200 800');
        this.svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');

        // Create groups for layers
        this.linesGroup = document.createElementNS(this.svgNS, 'g');
        this.linesGroup.id = 'patchlines';

        this.boxesGroup = document.createElementNS(this.svgNS, 'g');
        this.boxesGroup.id = 'boxes';

        this.svg.appendChild(this.linesGroup);
        this.svg.appendChild(this.boxesGroup);

        // Add event listeners for canvas interactions
        this.svg.addEventListener('mousedown', this.handleCanvasMouseDown.bind(this));
        this.svg.addEventListener('mousemove', this.handleCanvasMouseMove.bind(this));
        this.svg.addEventListener('mouseup', this.handleCanvasMouseUp.bind(this));
        this.svg.addEventListener('dblclick', this.handleCanvasDoubleClick.bind(this));

        canvas.appendChild(this.svg);
    }

    initializeControls() {
        // Connection mode toggle
        const connectionBtn = document.getElementById('connection-btn');
        if (connectionBtn) {
            connectionBtn.addEventListener('click', () => {
                this.connectionMode = !this.connectionMode;
                connectionBtn.classList.toggle('active', this.connectionMode);
                this.updateInfo(`Connection mode: ${this.connectionMode ? 'ON' : 'OFF'}`);
            });
        }

        // Create object button
        const createBtn = document.getElementById('create-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.createObjectDialog();
            });
        }
    }

    updateStatus(text, className) {
        const statusEl = document.getElementById('status');
        const statusText = statusEl.querySelector('.status-text');
        if (statusText) {
            statusText.textContent = text;
        }
        statusEl.className = className;
    }

    updateInfo(text) {
        const infoText = document.getElementById('info-text');
        if (infoText) {
            infoText.textContent = text;
        }
    }

    handleUpdate(data) {
        if (data.type === 'update') {
            // Update title
            if (data.title) {
                document.getElementById('title').textContent =
                    `py2max Interactive Editor - ${data.title}`;
            }

            // Clear current state
            this.boxes.clear();
            this.lines = [];

            // Update boxes
            data.boxes.forEach(box => {
                this.boxes.set(box.id, box);
            });

            // Update lines
            this.lines = data.lines || [];

            // Re-render
            this.render();

            // Update info
            this.updateInfo(`${this.boxes.size} objects · ${this.lines.length} connections`);
        }
    }

    render() {
        // Clear SVG
        this.linesGroup.innerHTML = '';
        this.boxesGroup.innerHTML = '';

        // Render patchlines first (behind boxes)
        this.lines.forEach(line => {
            const srcBox = this.boxes.get(line.src);
            const dstBox = this.boxes.get(line.dst);

            if (srcBox && dstBox) {
                const lineEl = this.createLine(srcBox, dstBox, line);
                this.linesGroup.appendChild(lineEl);
            }
        });

        // Render boxes
        this.boxes.forEach(box => {
            const boxEl = this.createBox(box);
            this.boxesGroup.appendChild(boxEl);
        });

        // Update viewBox to fit content
        this.updateViewBox();
    }

    createBox(box) {
        const g = document.createElementNS(this.svgNS, 'g');
        g.setAttribute('class', 'box');
        g.setAttribute('data-id', box.id);

        const x = box.x || 0;
        const y = box.y || 0;
        const width = box.width || 60;
        const height = box.height || 22;

        // Create rectangle
        const rect = document.createElementNS(this.svgNS, 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', width);
        rect.setAttribute('height', height);
        rect.setAttribute('fill', this.getBoxFill(box));
        rect.setAttribute('stroke', '#333');
        rect.setAttribute('stroke-width', '1');
        rect.setAttribute('rx', '3');

        // Create text
        const text = document.createElementNS(this.svgNS, 'text');
        text.setAttribute('x', x + 5);
        text.setAttribute('y', y + height / 2 + 4);
        text.setAttribute('fill', '#000');
        text.setAttribute('font-family', 'Monaco, Courier, monospace');
        text.setAttribute('font-size', '11');
        text.setAttribute('dominant-baseline', 'middle');

        const textContent = box.text || box.maxclass || '';
        text.textContent = textContent;

        // Add clipping
        const clipId = `clip-${box.id}`;
        const clipPath = document.createElementNS(this.svgNS, 'clipPath');
        clipPath.setAttribute('id', clipId);
        const clipRect = document.createElementNS(this.svgNS, 'rect');
        clipRect.setAttribute('x', x);
        clipRect.setAttribute('y', y);
        clipRect.setAttribute('width', width);
        clipRect.setAttribute('height', height);
        clipPath.appendChild(clipRect);

        const defs = this.svg.querySelector('defs') || this.createDefs();
        defs.appendChild(clipPath);
        text.setAttribute('clip-path', `url(#${clipId})`);

        g.appendChild(rect);
        g.appendChild(text);

        // Add ports
        if (box.inlet_count > 0 || box.outlet_count > 0) {
            this.addPorts(g, box);
        }

        // Add interaction handlers
        g.addEventListener('mousedown', (e) => this.handleBoxMouseDown(e, box));
        g.addEventListener('click', (e) => this.handleBoxClick(e, box));

        return g;
    }

    createDefs() {
        let defs = this.svg.querySelector('defs');
        if (!defs) {
            defs = document.createElementNS(this.svgNS, 'defs');
            this.svg.insertBefore(defs, this.svg.firstChild);
        }
        return defs;
    }

    addPorts(group, box) {
        const x = box.x || 0;
        const y = box.y || 0;
        const w = box.width || 60;
        const h = box.height || 22;

        // Draw inlets
        if (box.inlet_count > 0) {
            const spacing = w / (box.inlet_count + 1);
            for (let i = 0; i < box.inlet_count; i++) {
                const circle = document.createElementNS(this.svgNS, 'circle');
                circle.setAttribute('cx', x + spacing * (i + 1));
                circle.setAttribute('cy', y);
                circle.setAttribute('r', '3');
                circle.setAttribute('fill', '#4080ff');
                circle.setAttribute('stroke', '#333');
                circle.setAttribute('stroke-width', '0.5');
                circle.setAttribute('class', 'inlet');
                circle.setAttribute('data-index', i);
                group.appendChild(circle);
            }
        }

        // Draw outlets
        if (box.outlet_count > 0) {
            const spacing = w / (box.outlet_count + 1);
            for (let i = 0; i < box.outlet_count; i++) {
                const circle = document.createElementNS(this.svgNS, 'circle');
                circle.setAttribute('cx', x + spacing * (i + 1));
                circle.setAttribute('cy', y + h);
                circle.setAttribute('r', '3');
                circle.setAttribute('fill', '#ff8040');
                circle.setAttribute('stroke', '#333');
                circle.setAttribute('stroke-width', '0.5');
                circle.setAttribute('class', 'outlet');
                circle.setAttribute('data-index', i);
                group.appendChild(circle);
            }
        }
    }

    createLine(srcBox, dstBox, line) {
        const srcPoint = this.getPortPosition(srcBox, line.src_outlet || 0, true);
        const dstPoint = this.getPortPosition(dstBox, line.dst_inlet || 0, false);

        const lineEl = document.createElementNS(this.svgNS, 'line');
        lineEl.setAttribute('x1', srcPoint.x);
        lineEl.setAttribute('y1', srcPoint.y);
        lineEl.setAttribute('x2', dstPoint.x);
        lineEl.setAttribute('y2', dstPoint.y);
        lineEl.setAttribute('stroke', '#666');
        lineEl.setAttribute('stroke-width', '2');
        lineEl.setAttribute('stroke-linecap', 'round');

        return lineEl;
    }

    getPortPosition(box, portIndex, isOutlet) {
        const x = box.x || 0;
        const y = box.y || 0;
        const w = box.width || 60;
        const h = box.height || 22;

        if (isOutlet) {
            const count = box.outlet_count || 1;
            const spacing = w / (count + 1);
            return {
                x: x + spacing * (portIndex + 1),
                y: y + h
            };
        } else {
            const count = box.inlet_count || 1;
            const spacing = w / (count + 1);
            return {
                x: x + spacing * (portIndex + 1),
                y: y
            };
        }
    }

    getBoxFill(box) {
        if (box.maxclass === 'comment') return '#ffffd0';
        if (box.maxclass === 'message') return '#e0e0e0';
        return '#f0f0f0';
    }

    updateViewBox() {
        if (this.boxes.size === 0) {
            this.svg.setAttribute('viewBox', '0 0 1200 800');
            return;
        }

        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;

        this.boxes.forEach(box => {
            const x = box.x || 0;
            const y = box.y || 0;
            const w = box.width || 60;
            const h = box.height || 22;

            minX = Math.min(minX, x);
            minY = Math.min(minY, y);
            maxX = Math.max(maxX, x + w);
            maxY = Math.max(maxY, y + h);
        });

        const padding = 50;
        minX -= padding;
        minY -= padding;
        maxX += padding;
        maxY += padding;

        const width = maxX - minX;
        const height = maxY - minY;

        this.svg.setAttribute('viewBox', `${minX} ${minY} ${width} ${height}`);
    }

    // Event handlers for drag-and-drop

    handleBoxMouseDown(event, box) {
        if (this.connectionMode) {
            return;  // Don't start dragging in connection mode
        }

        event.stopPropagation();
        this.selectedBox = box;
        this.dragging = true;

        // Calculate offset from mouse to box top-left
        const svgPoint = this.getSVGPoint(event);
        this.dragOffset = {
            x: svgPoint.x - (box.x || 0),
            y: svgPoint.y - (box.y || 0)
        };
    }

    handleCanvasMouseMove(event) {
        if (this.dragging && this.selectedBox) {
            const svgPoint = this.getSVGPoint(event);

            // Update local box position immediately for smooth dragging
            this.selectedBox.x = svgPoint.x - this.dragOffset.x;
            this.selectedBox.y = svgPoint.y - this.dragOffset.y;

            // Re-render for immediate visual feedback
            this.render();
        }
    }

    handleCanvasMouseUp(event) {
        if (this.dragging && this.selectedBox) {
            // Send position update to server
            this.sendMessage({
                type: 'update_position',
                box_id: this.selectedBox.id,
                x: this.selectedBox.x,
                y: this.selectedBox.y
            });

            this.dragging = false;
            this.selectedBox = null;
        }
    }

    handleBoxClick(event, box) {
        if (this.connectionMode) {
            event.stopPropagation();

            if (!this.connectionStart) {
                // Start connection from this box
                this.connectionStart = box;
                this.updateInfo(`Connecting from ${box.text || box.id}... Click destination`);
            } else {
                // Complete connection to this box
                this.sendMessage({
                    type: 'create_connection',
                    src_id: this.connectionStart.id,
                    dst_id: box.id,
                    src_outlet: 0,
                    dst_inlet: 0
                });

                this.updateInfo(`Connected: ${this.connectionStart.text} → ${box.text}`);
                this.connectionStart = null;
            }
        }
    }

    handleCanvasDoubleClick(event) {
        const svgPoint = this.getSVGPoint(event);
        this.createObjectDialog(svgPoint.x, svgPoint.y);
    }

    handleCanvasMouseDown(event) {
        if (this.connectionMode && this.connectionStart) {
            // Cancel connection
            this.connectionStart = null;
            this.updateInfo('Connection cancelled');
        }
    }

    // Helper methods

    getSVGPoint(event) {
        const CTM = this.svg.getScreenCTM();
        return {
            x: (event.clientX - CTM.e) / CTM.a,
            y: (event.clientY - CTM.f) / CTM.d
        };
    }

    createObjectDialog(x, y) {
        const text = prompt('Enter object text:', 'newobj');
        if (text) {
            this.sendMessage({
                type: 'create_object',
                text: text,
                x: x || 100,
                y: y || 100
            });
        }
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.error('WebSocket not connected');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new InteractiveEditor();
});
