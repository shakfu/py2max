/**
 * py2max Live Preview - Client-side JavaScript
 * Uses Server-Sent Events (SSE) for real-time updates
 */

class LivePreview {
    constructor() {
        this.boxes = new Map();
        this.lines = [];
        this.eventSource = null;
        this.svgNS = 'http://www.w3.org/2000/svg';

        this.initializeSSE();
        this.initializeSVG();
    }

    initializeSSE() {
        const statusEl = document.getElementById('status');
        const statusText = statusEl.querySelector('.status-text');

        // Connect to SSE endpoint
        this.eventSource = new EventSource('/events');

        this.eventSource.onopen = () => {
            statusText.textContent = 'Connected';
            statusEl.className = 'connected';
            console.log('SSE connection opened');
        };

        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleUpdate(data);
        };

        this.eventSource.onerror = (error) => {
            statusText.textContent = 'Disconnected';
            statusEl.className = 'disconnected';
            console.error('SSE error:', error);

            // Attempt to reconnect
            setTimeout(() => {
                statusText.textContent = 'Reconnecting...';
                console.log('Attempting to reconnect...');
                this.initializeSSE();
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

        canvas.appendChild(this.svg);
    }

    handleUpdate(data) {
        if (data.type === 'update') {
            // Update title
            if (data.title) {
                document.getElementById('title').textContent =
                    `py2max Live Preview - ${data.title}`;
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
            this.updateInfo();
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

        // Create text with proper overflow handling
        const text = document.createElementNS(this.svgNS, 'text');
        text.setAttribute('x', x + 5);
        text.setAttribute('y', y + height / 2 + 4);
        text.setAttribute('fill', '#000');
        text.setAttribute('font-family', 'Monaco, Courier, monospace');
        text.setAttribute('font-size', '11');
        text.setAttribute('dominant-baseline', 'middle');

        const textContent = box.text || box.maxclass || '';
        text.textContent = textContent;

        // Add clipping path to prevent text overflow
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

        // Apply clipping to text
        text.setAttribute('clip-path', `url(#${clipId})`);

        g.appendChild(rect);
        g.appendChild(text);

        // Add ports if available
        if (box.inlet_count > 0 || box.outlet_count > 0) {
            this.addPorts(g, box);
        }

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
                group.appendChild(circle);
            }
        }
    }

    createLine(srcBox, dstBox, line) {
        // Calculate connection points
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

        // Add padding
        const padding = 50;
        minX -= padding;
        minY -= padding;
        maxX += padding;
        maxY += padding;

        const width = maxX - minX;
        const height = maxY - minY;

        this.svg.setAttribute('viewBox', `${minX} ${minY} ${width} ${height}`);
    }

    updateInfo() {
        const infoText = document.getElementById('info-text');
        if (infoText) {
            infoText.textContent = `${this.boxes.size} objects · ${this.lines.length} connections`;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new LivePreview();
});
