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
        this.selectedLine = null;  // Track selected patchline for deletion
        this.dragging = false;
        this.dragStarted = false;  // Track if drag actually started
        this.dragOffset = { x: 0, y: 0 };
        this.mouseDownPos = null;  // Track mouse down position

        // Connection state - tracks outlet -> inlet connections
        this.connectionStart = null;  // {box, portIndex, isOutlet}

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
        // Save button
        const saveBtn = document.getElementById('save-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.handleSave();
            });
        }

        // Create object button
        const createBtn = document.getElementById('create-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.createObjectDialog();
            });
        }

        // Keyboard handler for delete/backspace
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Delete' || e.key === 'Backspace') {
                e.preventDefault();  // Prevent browser back navigation
                this.handleDelete();
            }
        });

        // Note: Connection mode removed - click outlets/inlets directly
        // Click an outlet (bottom), then click an inlet (top) to connect
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

            // Update save button tooltip with filepath
            if (data.filepath) {
                const saveBtn = document.getElementById('save-btn');
                if (saveBtn) {
                    saveBtn.title = `Save patch to ${data.filepath}`;
                }
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
        } else if (data.type === 'save_complete') {
            this.updateInfo(`✅ Saved to ${data.filepath}`);
            console.log('Patch saved:', data.filepath);
        } else if (data.type === 'save_error') {
            this.updateInfo(`❌ Save error: ${data.message}`);
            console.error('Save error:', data.message);
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

                // Highlight if selected
                if (this.selectedLine &&
                    this.selectedLine.src === line.src &&
                    this.selectedLine.dst === line.dst &&
                    (this.selectedLine.src_outlet || 0) === (line.src_outlet || 0) &&
                    (this.selectedLine.dst_inlet || 0) === (line.dst_inlet || 0)) {
                    const visibleLine = lineEl.querySelector('.patchline');
                    if (visibleLine) {
                        visibleLine.setAttribute('stroke', '#ff8040');
                        visibleLine.setAttribute('stroke-width', '3');
                    }
                }

                this.linesGroup.appendChild(lineEl);
            }
        });

        // Render boxes
        this.boxes.forEach(box => {
            const boxEl = this.createBox(box);

            // Highlight if selected
            if (this.selectedBox && this.selectedBox.id === box.id) {
                // Add selected class to disable hover styling
                boxEl.classList.add('selected');
                const rect = boxEl.querySelector('rect');
                if (rect) {
                    rect.setAttribute('stroke', '#ff8040');
                    rect.setAttribute('stroke-width', '3');
                }
            }

            this.boxesGroup.appendChild(boxEl);
        });

        // Highlight selected port (inlet or outlet) if in connection mode
        if (this.connectionStart) {
            const portClass = this.connectionStart.isOutlet ? '.outlet' : '.inlet';
            const ports = this.boxesGroup.querySelectorAll(portClass);
            ports.forEach(port => {
                const parent = port.parentElement;
                const boxId = parent.getAttribute('data-id');
                const portIndex = parseInt(port.getAttribute('data-index'));

                if (boxId === this.connectionStart.box.id &&
                    portIndex === this.connectionStart.portIndex) {
                    port.classList.add('selected');
                }
            });
        }

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

        // Draw inlets (top of box)
        if (box.inlet_count > 0) {
            const spacing = w / (box.inlet_count + 1);
            for (let i = 0; i < box.inlet_count; i++) {
                const circle = document.createElementNS(this.svgNS, 'circle');
                circle.setAttribute('cx', x + spacing * (i + 1));
                circle.setAttribute('cy', y);
                circle.setAttribute('r', '4');
                circle.setAttribute('fill', '#4080ff');
                circle.setAttribute('stroke', '#333');
                circle.setAttribute('stroke-width', '1');
                circle.setAttribute('class', 'inlet port');
                circle.setAttribute('data-index', i);
                circle.style.cursor = 'pointer';

                // Add click handler for inlet
                circle.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.handlePortClick(box, i, false);  // false = inlet
                });

                group.appendChild(circle);
            }
        }

        // Draw outlets (bottom of box)
        if (box.outlet_count > 0) {
            const spacing = w / (box.outlet_count + 1);
            for (let i = 0; i < box.outlet_count; i++) {
                const circle = document.createElementNS(this.svgNS, 'circle');
                circle.setAttribute('cx', x + spacing * (i + 1));
                circle.setAttribute('cy', y + h);
                circle.setAttribute('r', '4');
                circle.setAttribute('fill', '#ff8040');
                circle.setAttribute('stroke', '#333');
                circle.setAttribute('stroke-width', '1');
                circle.setAttribute('class', 'outlet port');
                circle.setAttribute('data-index', i);
                circle.style.cursor = 'pointer';

                // Add click handler for outlet
                circle.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.handlePortClick(box, i, true);  // true = outlet
                });

                group.appendChild(circle);
            }
        }
    }

    createLine(srcBox, dstBox, line) {
        const srcPoint = this.getPortPosition(srcBox, line.src_outlet || 0, true);
        const dstPoint = this.getPortPosition(dstBox, line.dst_inlet || 0, false);

        // Create group for the line
        const g = document.createElementNS(this.svgNS, 'g');
        g.setAttribute('class', 'patchline-group');
        g.setAttribute('data-src', line.src);
        g.setAttribute('data-dst', line.dst);
        g.setAttribute('data-src-outlet', line.src_outlet || 0);
        g.setAttribute('data-dst-inlet', line.dst_inlet || 0);
        g.style.cursor = 'pointer';

        // Add invisible wider hitbox for easier clicking
        const hitbox = document.createElementNS(this.svgNS, 'line');
        hitbox.setAttribute('x1', srcPoint.x);
        hitbox.setAttribute('y1', srcPoint.y);
        hitbox.setAttribute('x2', dstPoint.x);
        hitbox.setAttribute('y2', dstPoint.y);
        hitbox.setAttribute('stroke', 'transparent');
        hitbox.setAttribute('stroke-width', '10');  // Wider for easier clicking
        hitbox.setAttribute('class', 'patchline-hitbox');

        // Visible line
        const lineEl = document.createElementNS(this.svgNS, 'line');
        lineEl.setAttribute('x1', srcPoint.x);
        lineEl.setAttribute('y1', srcPoint.y);
        lineEl.setAttribute('x2', dstPoint.x);
        lineEl.setAttribute('y2', dstPoint.y);
        lineEl.setAttribute('stroke', '#666');
        lineEl.setAttribute('stroke-width', '2');
        lineEl.setAttribute('stroke-linecap', 'round');
        lineEl.setAttribute('class', 'patchline');

        // Add click handler to the group (catches both hitbox and line clicks)
        g.addEventListener('click', (e) => {
            e.stopPropagation();
            this.handleLineClick(line);
        });

        // Append elements
        g.appendChild(hitbox);  // Hitbox first (behind)
        g.appendChild(lineEl);  // Visible line on top
        return g;
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
        // Don't handle if clicking on a port - let port handler deal with it
        if (event.target.classList.contains('port') ||
            event.target.classList.contains('inlet') ||
            event.target.classList.contains('outlet')) {
            return;
        }

        event.stopPropagation();

        // Prepare for potential drag
        this.dragging = true;
        this.dragStarted = false;  // Not started until movement

        const svgPoint = this.getSVGPoint(event);
        this.mouseDownPos = { x: svgPoint.x, y: svgPoint.y };

        // Calculate offset from mouse to box top-left
        this.dragOffset = {
            x: svgPoint.x - (box.x || 0),
            y: svgPoint.y - (box.y || 0)
        };

        // Store which box for potential drag or selection
        this.selectedBox = box;
        this.selectedLine = null;  // Deselect any line

        // Show selection immediately (before drag starts)
        this.render();
    }

    handleCanvasMouseMove(event) {
        if (this.dragging && this.selectedBox) {
            const svgPoint = this.getSVGPoint(event);

            // Check if we've moved enough to start dragging (5px threshold)
            if (!this.dragStarted && this.mouseDownPos) {
                const dx = Math.abs(svgPoint.x - this.mouseDownPos.x);
                const dy = Math.abs(svgPoint.y - this.mouseDownPos.y);
                if (dx > 5 || dy > 5) {
                    this.dragStarted = true;
                }
            }

            // Only update position if drag has actually started
            if (this.dragStarted) {
                // Update local box position immediately for smooth dragging
                this.selectedBox.x = svgPoint.x - this.dragOffset.x;
                this.selectedBox.y = svgPoint.y - this.dragOffset.y;

                // Re-render for immediate visual feedback
                this.render();
            }
        }
    }

    handleCanvasMouseUp(event) {
        if (this.dragging && this.selectedBox) {
            // If drag actually started, send position update
            if (this.dragStarted) {
                this.sendMessage({
                    type: 'update_position',
                    box_id: this.selectedBox.id,
                    x: this.selectedBox.x,
                    y: this.selectedBox.y
                });
                // Don't keep selection after drag
                this.selectedBox = null;
            } else {
                // Just a click (no drag) - keep selection and show visual feedback
                this.updateInfo(`Selected: ${this.selectedBox.text || this.selectedBox.id} (Press Delete to remove)`);
                this.render();  // Show selection highlighting
            }

            this.dragging = false;
            this.dragStarted = false;
            this.mouseDownPos = null;
        }
    }

    handlePortClick(box, portIndex, isOutlet) {
        if (!this.connectionStart) {
            // First click - can be either inlet or outlet
            this.connectionStart = {
                box: box,
                portIndex: portIndex,
                isOutlet: isOutlet
            };

            const portType = isOutlet ? 'outlet' : 'inlet';
            const nextType = isOutlet ? 'inlet' : 'outlet';
            this.updateInfo(`Connecting from ${box.text || box.id} ${portType} ${portIndex}... Click ${nextType}`);

            // Visual feedback - highlight the selected port
            this.render();
        } else {
            // Second click - must be opposite type from first click
            if (isOutlet === this.connectionStart.isOutlet) {
                const portType = isOutlet ? 'outlet' : 'inlet';
                const oppositeType = isOutlet ? 'inlet' : 'outlet';
                this.updateInfo(`Click an ${oppositeType}, not another ${portType}`);
                return;
            }

            // Determine source (outlet) and destination (inlet)
            let srcBox, dstBox, srcOutlet, dstInlet;

            if (this.connectionStart.isOutlet) {
                // Started from outlet, ending at inlet
                srcBox = this.connectionStart.box;
                srcOutlet = this.connectionStart.portIndex;
                dstBox = box;
                dstInlet = portIndex;
            } else {
                // Started from inlet, ending at outlet
                srcBox = box;
                srcOutlet = portIndex;
                dstBox = this.connectionStart.box;
                dstInlet = this.connectionStart.portIndex;
            }

            // Create connection
            this.sendMessage({
                type: 'create_connection',
                src_id: srcBox.id,
                dst_id: dstBox.id,
                src_outlet: srcOutlet,
                dst_inlet: dstInlet
            });

            this.updateInfo(`Connected: ${srcBox.text}[${srcOutlet}] → ${dstBox.text}[${dstInlet}]`);

            // Clear connection state
            this.connectionStart = null;
            this.render();
        }
    }

    handleCanvasDoubleClick(event) {
        const svgPoint = this.getSVGPoint(event);
        this.createObjectDialog(svgPoint.x, svgPoint.y);
    }

    handleLineClick(line) {
        // Select the line for deletion
        this.selectedLine = line;
        this.selectedBox = null;  // Deselect any box

        const srcBox = this.boxes.get(line.src);
        const dstBox = this.boxes.get(line.dst);
        this.updateInfo(`Selected connection: ${srcBox.text}[${line.src_outlet}] → ${dstBox.text}[${line.dst_inlet}] (Press Delete/Backspace to remove)`);

        // Re-render to show selection
        this.render();
    }

    handleCanvasMouseDown(event) {
        const target = event.target;

        // Check if clicking on a port - if so, don't deselect or cancel connection
        if (target.classList.contains('port') ||
            target.classList.contains('inlet') ||
            target.classList.contains('outlet')) {
            // Clicking on a port - let the port's click handler handle it
            return;
        }

        // Check if clicking on a line - if so, don't deselect
        if (target.classList.contains('patchline') ||
            target.classList.contains('patchline-hitbox') ||
            target.closest('.patchline-group')) {
            // Clicking on a line - don't deselect, let the line's click handler handle it
            return;
        }

        // Deselect everything when clicking on empty canvas
        this.selectedBox = null;
        this.selectedLine = null;

        // Cancel any pending connection
        if (this.connectionStart) {
            this.connectionStart = null;
            this.updateInfo('Connection cancelled');
        } else {
            this.updateInfo('');
        }

        this.render();
    }

    handleDelete() {
        if (this.selectedLine) {
            // Delete selected patchline
            this.sendMessage({
                type: 'delete_connection',
                src_id: this.selectedLine.src,
                dst_id: this.selectedLine.dst,
                src_outlet: this.selectedLine.src_outlet,
                dst_inlet: this.selectedLine.dst_inlet
            });

            this.updateInfo('Connection deleted');
            this.selectedLine = null;
        } else if (this.selectedBox) {
            // Delete selected box
            this.sendMessage({
                type: 'delete_object',
                box_id: this.selectedBox.id
            });

            this.updateInfo(`Deleted: ${this.selectedBox.text || this.selectedBox.id}`);
            this.selectedBox = null;
        } else {
            this.updateInfo('Nothing selected to delete');
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

    handleSave() {
        this.sendMessage({ type: 'save' });
        this.updateInfo('Saving...');
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
