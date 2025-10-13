# JavaScript Libraries Integration

This document describes the integration of SVG.js and WebCola libraries into the py2max interactive editor.

## Libraries

### 1. SVG.js (v3.2.5)

**Description**: A lightweight library for manipulating and animating SVG elements.

**Homepage**: <https://svgjs.dev/>

**Size**: 78KB (minified)

**Location**: `py2max/static/svg.min.js`

**Potential Uses**:

- Simplified SVG manipulation API
- Built-in animation support for smooth transitions
- Easier creation and modification of SVG elements
- Better handling of transformations and styling
- Path manipulation and morphing
- SVG filters and effects

**Current Status**: [x] **Active** - Fully integrated throughout the interactive editor.

**Implementation**:

- SVG creation and initialization
- All box rendering (rectangles, text, clipping)
- All connection line rendering
- Port rendering (inlets/outlets)
- Smooth animations for auto-layout
- Cleaner, more maintainable code

### 2. WebCola (Constraint-Based Layout)

**Description**: A force-directed graph layout engine with constraint-based positioning.

**Homepage**: <https://ialab.it.monash.edu/webcola/>

**Size**: 78KB (minified)

**Location**: `py2max/static/cola.min.js`

**Features**:

- Force-directed graph layout
- Constraint-based positioning
- Automatic overlap avoidance
- Hierarchical layout support
- Handles disconnected components
- Multiple layout algorithms

**Current Implementation**: [x] **Active**

The auto-layout feature using WebCola is now implemented in the interactive editor.

## Auto-Layout Feature (WebCola)

### Usage

1. **Load a patch** with the interactive editor:

   ```bash
   py2max serve your-patch.maxpat
   ```

2. **Click the " Auto-Layout" button** in the toolbar

3. **Adjust parameters** using the interactive controls panel:
   - **Link Distance** (50-300): Desired distance between connected objects
   - **Iterations** (10-200): Number of layout algorithm iterations (more = better convergence)
   - **Canvas Width** (400-1600): Layout canvas width
   - **Canvas Height** (300-1200): Layout canvas height
   - **Avoid Overlaps**: Toggle automatic overlap avoidance
   - **Constraint Preset**: Apply alignment constraints for structured layouts
     - **None**: No alignment constraints (natural force-directed layout)
     - **Horizontal Flow**: Align objects in horizontal rows
     - **Vertical Flow**: Align objects in vertical columns
     - **Grid**: Align objects in both rows and columns (grid structure)

4. **Click "Apply Layout"** to recompute with new parameters

5. **Watch** as WebCola arranges objects with smooth SVG.js animations, respecting the selected constraints

### How It Works

The `autoLayout()` method:

1. **Converts** boxes and connections into WebCola's graph format
2. **Applies** force-directed layout with constraints:
   - Avoids overlapping objects
   - Maintains reasonable connection lengths
   - Handles disconnected components
   - Respects object dimensions
3. **Updates** all object positions
4. **Sends** position updates to the server
5. **Re-renders** the patch with the new layout

### WebCola Configuration

The layout is now fully configurable via interactive sliders:

```javascript
// Get parameters from UI controls
const linkDistance = parseInt(document.getElementById('link-distance-slider')?.value || 100);
const iterations = parseInt(document.getElementById('iterations-slider')?.value || 50);
const canvasWidth = parseInt(document.getElementById('canvas-width-slider')?.value || 800);
const canvasHeight = parseInt(document.getElementById('canvas-height-slider')?.value || 600);
const avoidOverlaps = document.getElementById('avoid-overlaps-checkbox')?.checked !== false;

// Configure WebCola with user-selected parameters
const layout = cola.d3adaptor(d3)
    .size([canvasWidth, canvasHeight])  // User-adjustable canvas size
    .nodes(nodes)                        // Graph nodes (boxes)
    .links(links)                        // Graph edges (connections)
    .avoidOverlaps(avoidOverlaps)        // User-toggleable overlap avoidance
    .handleDisconnected(true)            // Handle separate components
    .jaccardLinkLengths(linkDistance)    // User-adjustable link length
    .start(iterations, iterations, iterations);  // User-adjustable iteration count
```

### Interactive Parameter Tuning

**Link Distance** (50-300) controls the natural length of connections:

- Lower values (50-100): Compact layouts, tighter clustering
- Higher values (150-300): Spread out layouts, more space between objects

**Iterations** (10-200) controls layout quality and convergence:

- Lower values (10-30): Faster but less optimal positioning
- Higher values (100-200): Slower but better convergence to ideal positions

**Canvas Size** (400-1600 × 300-1200) affects the available layout space:

- Adjust to match your patch complexity
- Larger canvas = more spread out objects

**Avoid Overlaps** (checkbox) ensures boxes don't overlap:

- Checked: Clean, readable layouts (recommended)
- Unchecked: Faster computation, allows overlaps

**Constraint Presets** create structured layouts using WebCola's constraint system:

1. **None** (default):
   - Natural force-directed layout
   - Objects arrange based purely on connections and spacing
   - Most flexible, adapts to any topology

2. **Horizontal Flow**:
   - Groups nearby objects into horizontal rows
   - All objects in a row share the same Y-coordinate
   - Ideal for left-to-right signal flow patches
   - Example: `[osc] → [filter] → [gain] → [dac~]` in a horizontal line

3. **Vertical Flow**:
   - Groups nearby objects into vertical columns
   - All objects in a column share the same X-coordinate
   - Ideal for top-to-bottom signal flow patches
   - Example: Stacked processing chain

4. **Grid**:
   - Combines both horizontal and vertical alignment
   - Creates a grid-like structure with aligned rows AND columns
   - Strictest layout, most organized appearance
   - Ideal for patches with clear functional groupings

### Constraint System Details

WebCola's constraint system uses **alignment constraints** to enforce structure:

```javascript
// Example: Horizontal Flow constraint
{
    type: 'alignment',
    axis: 'y',              // Align on Y-axis (horizontal row)
    offsets: [
        { node: 0, offset: 0 },
        { node: 1, offset: 0 },
        { node: 2, offset: 0 }
    ]
}
```

The constraint generation algorithm:

1. Analyzes current object positions
2. Groups objects within proximity threshold (50px)
3. Creates alignment constraints for each group
4. WebCola enforces constraints during layout computation

### Demo Scripts

Two demo scripts showcase the auto-layout feature:

#### 1. Complex Synthesizer Demo

```bash
python examples/auto_layout_demo.py
py2max serve outputs/auto_layout_demo.maxpat
```

Creates a complex synthesizer patch with:

- 13 objects (oscillators, filters, effects)
- 16 connections
- Random initial positions (messy!)

Click Auto-Layout to see WebCola organize it into a clean, readable layout.

#### 2. Hierarchical Layout Demo

```bash
py2max serve outputs/auto_layout_hierarchical.maxpat
```

Creates a hierarchical signal processing chain:

- 4 source oscillators
- 2 layers of processors
- Mixer and output
- 12 objects total

Demonstrates WebCola's ability to create hierarchical layouts that respect signal flow.

## Implementation Details

### File Modifications

**HTML** (`interactive.html`):

```html
<!-- External libraries -->
<script src="svg.min.js"></script>
<script src="cola.min.js"></script>

<!-- Auto-Layout button -->
<button id="auto-layout-btn" title="Auto-arrange objects"> Auto-Layout</button>
```

**JavaScript** (`interactive.js`):

SVG.js is now used throughout the editor for all SVG manipulation:

```javascript
// SVG initialization using SVG.js
initializeSVG() {
    this.draw = SVG().addTo('#canvas').size('100%', '100%');
    this.draw.viewbox(0, 0, 1200, 800);

    // Create groups for layers
    this.linesGroupSVG = this.draw.group().id('patchlines');
    this.boxesGroupSVG = this.draw.group().id('boxes');
}

// Box rendering using SVG.js (lines 278-325)
createBox(box) {
    const g = this.boxesGroupSVG.group();
    g.addClass('box').attr('data-id', box.id);

    // Rectangle
    g.rect(width, height)
        .move(x, y)
        .fill(this.getBoxFill(box))
        .stroke({ color: '#333', width: 1 })
        .radius(3);

    // Text with clipping
    const text = g.text(textContent)
        .move(x + 5, y + height / 2 + 4)
        .font({ family: 'Monaco, Courier, monospace', size: 11 });

    const clip = this.draw.clip().id(`clip-${box.id}`);
    clip.rect(width, height).move(x, y);
    text.clipWith(clip);
}

// Port rendering using SVG.js (lines 327-372)
addPorts(group, box) {
    // Inlets (top)
    const circle = group.circle(8)
        .center(cx, cy)
        .fill('#4080ff')
        .stroke({ color: '#333', width: 1 })
        .addClass('inlet port');
}

// Line rendering using SVG.js (lines 374-404)
createLine(srcBox, dstBox, line) {
    const g = this.linesGroupSVG.group();

    // Hitbox for easier clicking
    g.line(x1, y1, x2, y2)
        .stroke({ color: 'transparent', width: 10 });

    // Visible line
    g.line(x1, y1, x2, y2)
        .stroke({ color: '#666', width: 2, linecap: 'round' });
}
```

Auto-layout with WebCola and SVG.js animations (lines 806-915):

```javascript
autoLayout() {
    // 1. Prepare nodes and links for WebCola
    const nodes = [], links = [];
    this.boxes.forEach((box, boxId) => {
        nodes.push({ id: boxId, width: box.width, height: box.height, x: box.x, y: box.y });
    });

    // 2. Configure WebCola with D3
    const layout = cola.d3adaptor(d3)
        .size([800, 600])
        .nodes(nodes)
        .links(links)
        .avoidOverlaps(true)
        .jaccardLinkLengths(100);

    // 3. Run layout algorithm
    layout.start(50, 50, 50);

    // 4. Animate boxes to new positions using SVG.js
    nodes.forEach(node => {
        const boxElement = this.boxesGroup.querySelector(`[data-id="${node.id}"]`);
        const svgElement = SVG(boxElement);

        svgElement.animate(500, 0, 'now')
            .ease('<>')  // Ease in-out
            .transform({ translateX: newX - oldX, translateY: newY - oldY });
    });

    // 5. Re-render after animations complete
    Promise.all(animationPromises).then(() => this.render());
}
```

## Benefits

### WebCola Auto-Layout

**Pros**:

- [x] Instant organization of messy patches
- [x] Professional-looking layouts
- [x] Respects signal flow and connections
- [x] Avoids overlaps automatically
- [x] Handles complex graphs gracefully
- [x] Works with any patch size

**Use Cases**:

- Organizing imported/generated patches
- Cleaning up manually created patches
- Initial layout for new patches
- Educational demonstrations
- Screenshot/documentation preparation

### SVG.js Integration

**Current Benefits**:

- [x] Smoother animations (auto-layout transitions)
- [x] Cleaner code for SVG manipulation
- [x] Easier maintenance and readability
- [x] Better transform handling
- [x] Declarative API for all SVG elements

**Implemented Features**:

1. **SVG Initialization**: All SVG elements created via SVG.js
2. **Box Rendering**: Rectangles, text, clipping paths
3. **Connection Rendering**: Lines with hitboxes for interaction
4. **Port Rendering**: Inlet/outlet circles with proper styling
5. **Animations**: Smooth auto-layout transitions with easing

**Future Enhancement Ideas**:

1. **Animated dragging**: Smooth transitions when moving boxes manually
2. **Connection animations**: Animated line drawing from outlet to inlet
3. **Visual feedback**: Pulse effects, glow on hover
4. **Morphing**: Smooth box resize animations

## Performance Considerations

### WebCola

- **Small patches** (<20 objects): Instant layout
- **Medium patches** (20-100 objects): <1 second
- **Large patches** (>100 objects): 1-3 seconds
- **Iterations**: Configurable (default: 150 total)

The layout algorithm runs in the browser, so it doesn't block the server or other operations.

### SVG.js

- Minimal overhead (78KB minified)
- Only used when needed
- No performance impact when not actively animating

## Testing

### Automated Tests

All existing tests still pass with the libraries included:

```bash
make test
# 326 passed, 14 skipped
```

The libraries integrate seamlessly without breaking existing functionality.

### Manual Testing

To test the complete SVG.js and WebCola integration:

```bash
# 1. Start the interactive editor with a demo patch
py2max serve outputs/auto_layout_demo.maxpat

# 2. Open browser and test features:
# - Verify all boxes render correctly (SVG.js rendering)
# - Verify all connections render correctly (SVG.js lines)
# - Test dragging boxes (should be smooth)
# - Test selecting boxes/lines (should highlight)
# - Test creating connections (click outlet → inlet)
# - Click "Auto-Layout" button (should see smooth animations)
# - Test double-click on boxes to select
# - Press Delete/Backspace to remove selected items

# 3. Try the hierarchical demo
py2max serve outputs/auto_layout_hierarchical.maxpat
# Click Auto-Layout to see WebCola organize the tree structure
```

**Expected behavior:**

- All SVG elements render cleanly with proper styling
- Auto-layout produces smooth, animated transitions (500ms ease-in-out)
- Objects automatically arrange to avoid overlaps
- Connections maintain proper lengths
- Interactive controls panel appears when clicking Auto-Layout button
- Sliders update layout parameters in real-time
- "Apply Layout" button re-computes layout with new parameters
- No console errors

**Interactive Testing:**

1. Click " Auto-Layout" to show controls panel
2. Adjust **Link Distance** slider - watch layout spread/compress
3. Adjust **Iterations** slider - see convergence quality change
4. Adjust **Canvas Size** sliders - control available space
5. Toggle **Avoid Overlaps** - see overlapping behavior
6. **Try different Constraint Presets**:
   - Start with "None" - natural force-directed layout
   - Switch to "Horizontal Flow" - objects align in rows
   - Try "Vertical Flow" - objects align in columns
   - Select "Grid" - strict row and column alignment
7. Click "Apply Layout" to recompute with each parameter change
8. Click "Hide" to collapse the controls panel

**Constraint Preset Comparison:**

```bash
# Good test patch for constraints
py2max serve outputs/auto_layout_demo.maxpat

# Try each preset and observe:
# - None: Natural clustering, follows connections
# - Horizontal Flow: Signal chain flows left-to-right
# - Vertical Flow: Signal chain flows top-to-bottom
# - Grid: Clean grid structure, aligned rows AND columns
```

## Future Enhancements

### Short-term

- [ ] Add layout presets (hierarchical, circular, tree)
- [ ] Allow users to select layout algorithm
- [ ] Add undo/redo for layout changes
- [ ] Preserve aspect ratios during layout

### Medium-term

- [ ] Use SVG.js for smooth drag animations
- [ ] Animated connection drawing
- [ ] Visual effects for feedback (selection, hover)
- [ ] Export layouts as reusable templates

### Long-term

- [ ] Custom constraint specification (user-defined)
- [ ] Layout groups/clusters separately
- [ ] Integration with Python-side layout managers
- [ ] Machine learning-based layout optimization

## Conclusion

The py2max interactive editor now features complete integration of three powerful JavaScript libraries:

1. **D3.js (v7)** - Data visualization foundation for WebCola
2. **SVG.js (v3.2.5)** - Complete SVG manipulation and animation
3. **WebCola** - Force-directed graph layout with constraint-based positioning

### What's Working Now

**SVG.js Integration** ([x] Complete):

- All SVG elements created via SVG.js declarative API
- Cleaner, more maintainable rendering code
- Smooth animations for auto-layout transitions
- Better transform and styling handling

**WebCola Auto-Layout** ([x] Active):

- One-click automatic patch organization with interactive parameter controls
- Force-directed layout respects connections
- Real-time parameter adjustment via sliders:
  - Link Distance (50-300)
  - Iterations (10-200)
  - Canvas Size (adjustable width/height)
  - Avoid Overlaps (toggle)
  - Constraint Presets (None, Horizontal Flow, Vertical Flow, Grid)
- Constraint-based layouts for structured arrangements
- Handles disconnected components gracefully
- Works with any patch size

### Impact

These libraries transform the interactive editor from basic SVG manipulation to a polished, production-ready tool with:

- Professional animated transitions (SVG.js)
- Intelligent automatic layout (WebCola + D3)
- Interactive parameter tuning via sliders
- Constraint-based structured layouts
- Real-time layout experimentation
- Four layout presets for different use cases
- Clean, maintainable codebase
- Minimal overhead (234KB total, minified)

All three libraries are well-maintained, widely used in production, and integrate seamlessly with the existing py2max architecture.
