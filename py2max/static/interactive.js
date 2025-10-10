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

        // Store original box positions for reset functionality
        this.originalPositions = new Map();

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

        // Create SVG using SVG.js library
        this.draw = SVG().addTo('#canvas').size('100%', '100%');
        this.draw.viewbox(0, 0, 1200, 800);
        this.draw.attr('preserveAspectRatio', 'xMidYMid meet');

        // Get the native SVG element for event listeners
        this.svg = this.draw.node;

        // Create groups for layers using SVG.js
        this.linesGroupSVG = this.draw.group().id('patchlines');
        this.boxesGroupSVG = this.draw.group().id('boxes');

        // Get native DOM elements for compatibility with existing code
        this.linesGroup = this.linesGroupSVG.node;
        this.boxesGroup = this.boxesGroupSVG.node;

        // Add event listeners for canvas interactions
        this.svg.addEventListener('mousedown', this.handleCanvasMouseDown.bind(this));
        this.svg.addEventListener('mousemove', this.handleCanvasMouseMove.bind(this));
        this.svg.addEventListener('mouseup', this.handleCanvasMouseUp.bind(this));
        this.svg.addEventListener('dblclick', this.handleCanvasDoubleClick.bind(this));

        // Use event delegation for box double-clicks (since boxes are recreated on render)
        this.boxesGroup.addEventListener('dblclick', this.handleBoxesGroupDoubleClick.bind(this));

        console.log('SVG.js initialized:', SVG);
    }

    initializeControls() {
        // Load layout mode preference from localStorage (default to sidebar)
        const savedMode = localStorage.getItem('layoutControlsMode') || 'sidebar';
        if (savedMode === 'sidebar') {
            document.body.classList.add('sidebar-mode');
        }

        // Toggle layout mode button - switch between panel and sidebar
        const toggleLayoutModeBtn = document.getElementById('toggle-layout-mode-btn');
        if (toggleLayoutModeBtn) {
            // Update button text based on current mode
            this.updateLayoutModeButton();

            toggleLayoutModeBtn.addEventListener('click', () => {
                document.body.classList.toggle('sidebar-mode');
                this.updateLayoutModeButton();

                // Save preference
                const mode = document.body.classList.contains('sidebar-mode') ? 'sidebar' : 'panel';
                localStorage.setItem('layoutControlsMode', mode);
            });
        }

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

        // Parent button - navigate to parent patcher
        const parentBtn = document.getElementById('parent-btn');
        if (parentBtn) {
            parentBtn.addEventListener('click', () => {
                this.navigateToParent();
            });
        }

        // Auto-layout button - toggle layout controls panel
        const autoLayoutBtn = document.getElementById('auto-layout-btn');
        if (autoLayoutBtn) {
            autoLayoutBtn.addEventListener('click', () => {
                const controlsPanel = document.getElementById('layout-controls');
                const isSidebarMode = document.body.classList.contains('sidebar-mode');

                controlsPanel.classList.toggle('visible');

                // In sidebar mode, also toggle the controls-visible class on body for canvas padding
                if (isSidebarMode) {
                    document.body.classList.toggle('controls-visible');
                }

                // If panel just became visible, apply layout immediately
                if (controlsPanel.classList.contains('visible')) {
                    this.autoLayout();
                }
            });
        }

        // Initialize layout controls
        this.initializeLayoutControls();

        // Keyboard handler for delete/backspace and ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Delete' || e.key === 'Backspace') {
                e.preventDefault();  // Prevent browser back navigation
                this.handleDelete();
            } else if (e.key === 'Escape') {
                // ESC key navigates to parent patcher
                this.navigateToParent();
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

    updateLayoutModeButton() {
        const toggleBtn = document.getElementById('toggle-layout-mode-btn');
        if (toggleBtn) {
            const isSidebarMode = document.body.classList.contains('sidebar-mode');
            toggleBtn.textContent = isSidebarMode ? '📋 Panel Mode' : '⚙️ Sidebar Mode';
            toggleBtn.title = isSidebarMode
                ? 'Switch to horizontal panel layout'
                : 'Switch to right sidebar layout';
        }
    }

    handleUpdate(data) {
        if (data.type === 'update') {
            // Update title
            const patcherTitle = data.patcher_title || 'Untitled';
            document.getElementById('title').textContent =
                `py2max Interactive Editor - ${patcherTitle}`;

            // Update breadcrumb
            if (data.patcher_path && data.patcher_path.length > 0) {
                const breadcrumbPath = document.getElementById('breadcrumb-path');
                if (breadcrumbPath) {
                    breadcrumbPath.textContent = data.patcher_path.join(' / ');
                }
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
                // Flatten patching_rect into box properties for easier access
                if (box.patching_rect) {
                    box.x = box.patching_rect.x;
                    box.y = box.patching_rect.y;
                    box.width = box.patching_rect.w;
                    box.height = box.patching_rect.h;
                }
                this.boxes.set(box.id, box);

                // Save original position if not already saved
                if (!this.originalPositions.has(box.id)) {
                    this.originalPositions.set(box.id, {
                        x: box.x,
                        y: box.y
                    });
                }
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
        // Clear SVG using SVG.js
        this.linesGroupSVG.clear();
        this.boxesGroupSVG.clear();

        // Render patchlines first (behind boxes)
        this.lines.forEach(line => {
            const srcBox = this.boxes.get(line.src);
            const dstBox = this.boxes.get(line.dst);

            if (srcBox && dstBox) {
                const lineGroup = this.createLine(srcBox, dstBox, line);

                // Highlight if selected
                if (this.selectedLine &&
                    this.selectedLine.src === line.src &&
                    this.selectedLine.dst === line.dst &&
                    (this.selectedLine.src_outlet || 0) === (line.src_outlet || 0) &&
                    (this.selectedLine.dst_inlet || 0) === (line.dst_inlet || 0)) {
                    // Find the visible line element
                    const visibleLine = lineGroup.node.querySelector('.patchline');
                    if (visibleLine) {
                        SVG(visibleLine).stroke({ color: '#ff8040', width: 3 });
                    }
                }
            }
        });

        // Render boxes
        this.boxes.forEach(box => {
            const boxGroup = this.createBox(box);

            // Highlight if selected
            if (this.selectedBox && this.selectedBox.id === box.id) {
                // Add selected class to disable hover styling
                boxGroup.node.classList.add('selected');
                const rect = boxGroup.node.querySelector('rect');
                if (rect) {
                    SVG(rect).stroke({ color: '#ff8040', width: 3 });
                }
            }
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
        // Create group using SVG.js
        const g = this.boxesGroupSVG.group();
        g.addClass('box');
        g.attr('data-id', box.id);

        // Add special class for boxes with subpatchers
        if (box.has_subpatcher) {
            g.addClass('has-subpatcher');
        }

        const x = box.x || 0;
        const y = box.y || 0;
        const width = box.width || 60;
        const height = box.height || 22;

        // Create rectangle using SVG.js
        const rect = g.rect(width, height)
            .move(x, y)
            .fill(this.getBoxFill(box))
            .stroke({ color: '#333', width: 1 })
            .radius(3);

        // Create text using SVG.js
        const textContent = box.text || box.maxclass || '';
        const text = g.text(textContent)
            .attr({ x: x + 5, y: y + height / 2 + 4 })
            .fill('#000')
            .font({ family: 'Monaco, Courier, monospace', size: 11 })
            .attr('dominant-baseline', 'middle');

        // Add clipping using SVG.js
        const clipId = `clip-${box.id}`;
        const clip = this.draw.clip().id(clipId);
        clip.rect(width, height).move(x, y);
        text.clipWith(clip);

        // Add ports
        if (box.inlet_count > 0 || box.outlet_count > 0) {
            this.addPorts(g, box);
        }

        // Add interaction handlers to native DOM node
        g.node.addEventListener('mousedown', (e) => this.handleBoxMouseDown(e, box));
        // Note: dblclick is now handled via event delegation on boxesGroup

        return g;
    }

    addPorts(group, box) {
        const x = box.x || 0;
        const y = box.y || 0;
        const w = box.width || 60;
        const h = box.height || 22;

        // Draw inlets (top of box) using SVG.js
        if (box.inlet_count > 0) {
            const spacing = w / (box.inlet_count + 1);
            for (let i = 0; i < box.inlet_count; i++) {
                const circle = group.circle(8)  // diameter = 8, radius = 4
                    .center(x + spacing * (i + 1), y)
                    .fill('#4080ff')
                    .stroke({ color: '#333', width: 1 })
                    .addClass('inlet port')
                    .attr('data-index', i)
                    .css('cursor', 'pointer');

                // Add click handler for inlet (on native DOM node)
                circle.node.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.handlePortClick(box, i, false);  // false = inlet
                });
            }
        }

        // Draw outlets (bottom of box) using SVG.js
        if (box.outlet_count > 0) {
            const spacing = w / (box.outlet_count + 1);
            for (let i = 0; i < box.outlet_count; i++) {
                const circle = group.circle(8)  // diameter = 8, radius = 4
                    .center(x + spacing * (i + 1), y + h)
                    .fill('#ff8040')
                    .stroke({ color: '#333', width: 1 })
                    .addClass('outlet port')
                    .attr('data-index', i)
                    .css('cursor', 'pointer');

                // Add click handler for outlet (on native DOM node)
                circle.node.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.handlePortClick(box, i, true);  // true = outlet
                });
            }
        }
    }

    createLine(srcBox, dstBox, line) {
        const srcPoint = this.getPortPosition(srcBox, line.src_outlet || 0, true);
        const dstPoint = this.getPortPosition(dstBox, line.dst_inlet || 0, false);

        // Create group for the line using SVG.js
        const g = this.linesGroupSVG.group();
        g.addClass('patchline-group');
        g.attr('data-src', line.src);
        g.attr('data-dst', line.dst);
        g.attr('data-src-outlet', line.src_outlet || 0);
        g.attr('data-dst-inlet', line.dst_inlet || 0);
        g.css('cursor', 'pointer');

        // Add invisible wider hitbox for easier clicking using SVG.js
        const hitbox = g.line(srcPoint.x, srcPoint.y, dstPoint.x, dstPoint.y)
            .stroke({ color: 'transparent', width: 10 })
            .addClass('patchline-hitbox');

        // Visible line using SVG.js
        const lineEl = g.line(srcPoint.x, srcPoint.y, dstPoint.x, dstPoint.y)
            .stroke({ color: '#666', width: 2, linecap: 'round' })
            .addClass('patchline');

        // Add click handler to the group (catches both hitbox and line clicks)
        g.node.addEventListener('click', (e) => {
            e.stopPropagation();
            this.handleLineClick(line);
        });

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

        // Ensure viewBox doesn't shift below/left of origin
        // Keep at least some visible area starting from (0, 0)
        minX = Math.min(minX, 0);
        minY = Math.min(minY, 0);

        // Ensure minimum viewBox size to prevent cramped layouts
        // Read from sliders if available, otherwise use defaults
        const minViewWidth = parseInt(document.getElementById('min-viewbox-width-slider')?.value || 800);
        const minViewHeight = parseInt(document.getElementById('min-viewbox-height-slider')?.value || 600);

        let width = Math.max(maxX - minX, minViewWidth);
        let height = Math.max(maxY - minY, minViewHeight);

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

        // Stop propagation for ALL boxes to prevent canvas handler from running
        event.stopPropagation();

        // Enable dragging for all boxes (including subpatchers)
        // Double-click still works via event delegation
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

    // Navigation methods

    handleBoxDoubleClick(event, box) {
        event.stopPropagation();
        event.preventDefault();

        // If box has subpatcher, navigate to it
        if (box.has_subpatcher) {
            this.navigateToSubpatcher(box.id);
        }
    }

    handleBoxesGroupDoubleClick(event) {
        // Event delegation: find which box was double-clicked
        let target = event.target;
        let boxElement = null;

        // Walk up the DOM tree to find the box group element
        while (target && target !== this.boxesGroup) {
            if (target.classList && target.classList.contains('box')) {
                boxElement = target;
                break;
            }
            target = target.parentElement;
        }

        if (boxElement) {
            const boxId = boxElement.getAttribute('data-id');
            const box = this.boxes.get(boxId);

            if (box && box.has_subpatcher) {
                event.stopPropagation();
                event.preventDefault();
                this.navigateToSubpatcher(box.id);
            }
        }
    }

    navigateToSubpatcher(boxId) {
        this.sendMessage({
            type: 'navigate_to_subpatcher',
            box_id: boxId
        });
        this.updateInfo('Navigating to subpatcher...');
    }

    navigateToParent() {
        this.sendMessage({
            type: 'navigate_to_parent'
        });
        this.updateInfo('Navigating to parent...');
    }

    navigateToRoot() {
        this.sendMessage({
            type: 'navigate_to_root'
        });
        this.updateInfo('Navigating to root...');
    }

    initializeLayoutControls() {
        // Link Distance slider
        const linkDistanceSlider = document.getElementById('link-distance-slider');
        const linkDistanceValue = document.getElementById('link-distance-value');
        if (linkDistanceSlider && linkDistanceValue) {
            linkDistanceSlider.addEventListener('input', (e) => {
                linkDistanceValue.textContent = e.target.value;
            });
        }

        // Iterations slider
        const iterationsSlider = document.getElementById('iterations-slider');
        const iterationsValue = document.getElementById('iterations-value');
        if (iterationsSlider && iterationsValue) {
            iterationsSlider.addEventListener('input', (e) => {
                iterationsValue.textContent = e.target.value;
            });
        }

        // Canvas Width slider
        const canvasWidthSlider = document.getElementById('canvas-width-slider');
        const canvasWidthValue = document.getElementById('canvas-width-value');
        if (canvasWidthSlider && canvasWidthValue) {
            canvasWidthSlider.addEventListener('input', (e) => {
                canvasWidthValue.textContent = e.target.value;
            });
        }

        // Canvas Height slider
        const canvasHeightSlider = document.getElementById('canvas-height-slider');
        const canvasHeightValue = document.getElementById('canvas-height-value');
        if (canvasHeightSlider && canvasHeightValue) {
            canvasHeightSlider.addEventListener('input', (e) => {
                canvasHeightValue.textContent = e.target.value;
            });
        }

        // Min ViewBox Width slider
        const minViewboxWidthSlider = document.getElementById('min-viewbox-width-slider');
        const minViewboxWidthValue = document.getElementById('min-viewbox-width-value');
        if (minViewboxWidthSlider && minViewboxWidthValue) {
            minViewboxWidthSlider.addEventListener('input', (e) => {
                minViewboxWidthValue.textContent = e.target.value;
                this.render();  // Re-render to update viewBox
            });
        }

        // Min ViewBox Height slider
        const minViewboxHeightSlider = document.getElementById('min-viewbox-height-slider');
        const minViewboxHeightValue = document.getElementById('min-viewbox-height-value');
        if (minViewboxHeightSlider && minViewboxHeightValue) {
            minViewboxHeightSlider.addEventListener('input', (e) => {
                minViewboxHeightValue.textContent = e.target.value;
                this.render();  // Re-render to update viewBox
            });
        }

        // Flow Spacing slider
        const flowSpacingSlider = document.getElementById('flow-spacing-slider');
        const flowSpacingValue = document.getElementById('flow-spacing-value');
        if (flowSpacingSlider && flowSpacingValue) {
            flowSpacingSlider.addEventListener('input', (e) => {
                flowSpacingValue.textContent = e.target.value;
            });
        }

        // Apply Layout button
        const applyLayoutBtn = document.getElementById('apply-layout-btn');
        if (applyLayoutBtn) {
            applyLayoutBtn.addEventListener('click', () => {
                this.autoLayout();
            });
        }

        // Reset Layout button
        const resetLayoutBtn = document.getElementById('reset-layout-btn');
        if (resetLayoutBtn) {
            resetLayoutBtn.addEventListener('click', () => {
                this.resetLayout();
            });
        }
    }

    reverseFlowLayout(nodes, axis, canvasWidth, canvasHeight) {
        /**
         * Reverse the flow layout by flipping coordinates along the specified axis.
         * For 'x' axis: flip horizontally (right-to-left)
         * For 'y' axis: flip vertically (bottom-to-top)
         */
        if (axis === 'x') {
            // Flip horizontally: mirror around vertical center
            const centerX = canvasWidth / 2;
            nodes.forEach(node => {
                const distanceFromCenter = node.x - centerX;
                node.x = centerX - distanceFromCenter;
            });
        } else if (axis === 'y') {
            // Flip vertically: mirror around horizontal center
            const centerY = canvasHeight / 2;
            nodes.forEach(node => {
                const distanceFromCenter = node.y - centerY;
                node.y = centerY - distanceFromCenter;
            });
        }
    }

    generateConstraints(nodes, preset) {
        const constraints = [];

        if (preset === 'none' || nodes.length === 0) {
            return constraints;
        }

        // Sort nodes by their current position for alignment
        const sortedByY = [...nodes].sort((a, b) => a.y - b.y);
        const sortedByX = [...nodes].sort((a, b) => a.x - b.x);

        if (preset === 'horizontal-flow') {
            // Align nodes in horizontal rows (same y coordinate for groups)
            // Group nodes into rows based on Y proximity
            const rows = [];
            const threshold = 50; // Y-distance threshold for same row

            sortedByY.forEach(node => {
                let addedToRow = false;
                for (let row of rows) {
                    const avgY = row.reduce((sum, n) => sum + n.y, 0) / row.length;
                    if (Math.abs(node.y - avgY) < threshold) {
                        row.push(node);
                        addedToRow = true;
                        break;
                    }
                }
                if (!addedToRow) {
                    rows.push([node]);
                }
            });

            // Create alignment constraints for each row
            rows.forEach(row => {
                if (row.length > 1) {
                    constraints.push({
                        type: 'alignment',
                        axis: 'y',
                        offsets: row.map(n => ({ node: nodes.indexOf(n), offset: 0 }))
                    });
                }
            });

        } else if (preset === 'vertical-flow') {
            // Align nodes in vertical columns (same x coordinate for groups)
            const columns = [];
            const threshold = 50; // X-distance threshold for same column

            sortedByX.forEach(node => {
                let addedToColumn = false;
                for (let column of columns) {
                    const avgX = column.reduce((sum, n) => sum + n.x, 0) / column.length;
                    if (Math.abs(node.x - avgX) < threshold) {
                        column.push(node);
                        addedToColumn = true;
                        break;
                    }
                }
                if (!addedToColumn) {
                    columns.push([node]);
                }
            });

            // Create alignment constraints for each column
            columns.forEach(column => {
                if (column.length > 1) {
                    constraints.push({
                        type: 'alignment',
                        axis: 'x',
                        offsets: column.map(n => ({ node: nodes.indexOf(n), offset: 0 }))
                    });
                }
            });

        } else if (preset === 'grid') {
            // Create both horizontal and vertical alignment constraints
            // This creates a grid-like structure

            // Horizontal alignment (rows)
            const rows = [];
            const yThreshold = 50;

            sortedByY.forEach(node => {
                let addedToRow = false;
                for (let row of rows) {
                    const avgY = row.reduce((sum, n) => sum + n.y, 0) / row.length;
                    if (Math.abs(node.y - avgY) < yThreshold) {
                        row.push(node);
                        addedToRow = true;
                        break;
                    }
                }
                if (!addedToRow) {
                    rows.push([node]);
                }
            });

            rows.forEach(row => {
                if (row.length > 1) {
                    constraints.push({
                        type: 'alignment',
                        axis: 'y',
                        offsets: row.map(n => ({ node: nodes.indexOf(n), offset: 0 }))
                    });
                }
            });

            // Vertical alignment (columns)
            const columns = [];
            const xThreshold = 50;

            sortedByX.forEach(node => {
                let addedToColumn = false;
                for (let column of columns) {
                    const avgX = column.reduce((sum, n) => sum + n.x, 0) / column.length;
                    if (Math.abs(node.x - avgX) < xThreshold) {
                        column.push(node);
                        addedToColumn = true;
                        break;
                    }
                }
                if (!addedToColumn) {
                    columns.push([node]);
                }
            });

            columns.forEach(column => {
                if (column.length > 1) {
                    constraints.push({
                        type: 'alignment',
                        axis: 'x',
                        offsets: column.map(n => ({ node: nodes.indexOf(n), offset: 0 }))
                    });
                }
            });
        }

        console.log(`Generated ${constraints.length} constraints for preset: ${preset}`);
        return constraints;
    }

    resetLayout() {
        /**
         * Reset all boxes to their original positions from when the patch was loaded.
         */
        if (this.originalPositions.size === 0) {
            this.updateInfo('No original positions to reset to');
            return;
        }

        this.updateInfo('Resetting to original layout...');

        // Restore original positions for all boxes
        this.boxes.forEach((box, boxId) => {
            const original = this.originalPositions.get(boxId);
            if (original) {
                box.x = original.x;
                box.y = original.y;

                // Send position update to server
                this.sendMessage({
                    type: 'update_position',
                    box_id: boxId,
                    x: original.x,
                    y: original.y
                });
            }
        });

        // Re-render to show updated positions
        this.render();
        this.updateInfo(`Reset ${this.originalPositions.size} objects to original positions`);
    }

    autoLayout() {
        // Use WebCola for force-directed graph layout
        if (typeof cola === 'undefined') {
            console.error('WebCola library not loaded');
            this.updateInfo('Error: WebCola library not available');
            return;
        }

        if (this.boxes.size === 0) {
            this.updateInfo('No objects to layout');
            return;
        }

        // Get parameters from controls
        const linkDistance = parseInt(document.getElementById('link-distance-slider')?.value || 100);
        const iterations = parseInt(document.getElementById('iterations-slider')?.value || 50);
        const canvasWidth = parseInt(document.getElementById('canvas-width-slider')?.value || 800);
        const canvasHeight = parseInt(document.getElementById('canvas-height-slider')?.value || 600);
        const avoidOverlaps = document.getElementById('avoid-overlaps-checkbox')?.checked !== false;
        const constraintPreset = document.getElementById('constraint-preset')?.value || 'none';
        const flowDirection = document.getElementById('flow-direction')?.value || 'none';
        const flowSpacing = parseInt(document.getElementById('flow-spacing-slider')?.value || 150);

        // Use sensible default for convergence threshold (not exposed in UI)
        const convergenceThreshold = 1e-3;

        this.updateInfo(`Computing auto-layout (linkDistance: ${linkDistance}, iterations: ${iterations}, flow: ${flowDirection})...`);

        // Prepare nodes and links for WebCola
        const nodes = [];
        const links = [];
        const nodeMap = new Map();

        // Create nodes array
        let index = 0;
        this.boxes.forEach((box, boxId) => {
            nodes.push({
                id: boxId,
                width: box.width || 60,
                height: box.height || 22,
                x: box.x || 0,
                y: box.y || 0,
                fixed: 0  // Not fixed
            });
            nodeMap.set(boxId, index++);
        });

        // Create links array from patchlines
        this.lines.forEach(line => {
            const sourceIdx = nodeMap.get(line.src);
            const targetIdx = nodeMap.get(line.dst);
            if (sourceIdx !== undefined && targetIdx !== undefined) {
                links.push({
                    source: sourceIdx,
                    target: targetIdx,
                    length: linkDistance  // Use slider value
                });
            }
        });

        // Generate constraints based on preset
        const constraints = this.generateConstraints(nodes, constraintPreset);

        // Configure WebCola using d3adaptor with parameters from sliders
        const layout = cola.d3adaptor(d3)
            .convergenceThreshold(convergenceThreshold)
            .size([canvasWidth, canvasHeight])
            .nodes(nodes)
            .links(links)
            .avoidOverlaps(avoidOverlaps)
            .handleDisconnected(true)
            .jaccardLinkLengths(linkDistance);

        // Determine if flow direction is reversed
        const isReversed = flowDirection.endsWith('-reverse');
        const baseFlowAxis = isReversed ? flowDirection.replace('-reverse', '') : flowDirection;

        // Apply flow layout if direction is specified
        if (flowDirection !== 'none') {
            layout.flowLayout(baseFlowAxis, flowSpacing);
        }

        // Apply constraints if any
        if (constraints.length > 0) {
            layout.constraints(constraints);
        }

        // Run the layout algorithm with custom iteration count
        layout.start(iterations, iterations, iterations);

        // If flow direction is reversed, flip the coordinates
        if (isReversed) {
            this.reverseFlowLayout(nodes, baseFlowAxis, canvasWidth, canvasHeight);
        }

        // Update box positions with smooth SVG.js animations

        const animationPromises = [];

        nodes.forEach(node => {
            const box = this.boxes.get(node.id);
            if (box) {
                const oldX = box.x || 0;
                const oldY = box.y || 0;
                const newX = Math.round(node.x);
                const newY = Math.round(node.y);

                // Update internal state
                box.x = newX;
                box.y = newY;

                // Find the SVG element for this box
                const boxElement = this.boxesGroup.querySelector(`[data-id="${node.id}"]`);

                if (boxElement) {
                    // Use SVG.js to animate the transform
                    const svgElement = SVG(boxElement);
                    const promise = new Promise(resolve => {
                        svgElement.animate(500, 0, 'now')
                            .ease('<>')  // Ease in-out
                            .transform({ translateX: newX - oldX, translateY: newY - oldY })
                            .after(() => {
                                // After animation, update actual position and reset transform
                                resolve();
                            });
                    });
                    animationPromises.push(promise);
                }

                // Send position update to server
                this.sendMessage({
                    type: 'update_position',
                    box_id: node.id,
                    x: box.x,
                    y: box.y
                });
            }
        });

        // Wait for animations to complete, then re-render
        Promise.all(animationPromises).then(() => {
            console.log('Animations complete, re-rendering...');
            this.render();
            const constraintInfo = constraints.length > 0 ? `, ${constraints.length} constraints` : '';
            const flowInfo = flowDirection !== 'none' ? `, flow: ${flowDirection} (${flowSpacing}px)` : '';
            this.updateInfo(`Auto-layout applied: ${nodes.length} objects, linkDistance: ${linkDistance}, iterations: ${iterations}${flowInfo}${constraintInfo}`);
        });
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
