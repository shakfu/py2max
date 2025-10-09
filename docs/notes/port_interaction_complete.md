# Port Interaction - Complete Solution

## Overview

This document consolidates all the fixes required to make port (inlet/outlet) interactions work correctly in the interactive SVG editor, without interference from box selection and hover states.

## Problems Encountered

### Problem 1: Box Hover Overrides Port Hover
When hovering over a port, the entire box showed a blue outline, making it unclear that the port was the interactive element.

### Problem 2: Box Selection Prevents Port Clicks
When clicking a port, the box's `mousedown` handler was selecting the box instead of letting the port's click handler execute.

### Problem 3: Canvas Handler Cancels Connections
When clicking a port, the canvas's `mousedown` handler was clearing `connectionStart`, preventing the connection from being created.

### Problem 4: Selected Box Hover Overrides Selection Color
When a box was selected, hovering over it showed blue outline instead of maintaining the orange selection color.

## Complete Solution

### 1. CSS: Disable Box Hover When Hovering Ports

**File:** `py2max/static/interactive.html` (lines 131-147)

```css
/* Normal box hover (when not hovering ports) */
.box:hover rect {
    stroke: #4080ff;
    stroke-width: 2;
}

/* Disable box hover when hovering over ports - ports have their own hover */
.box:has(.port:hover) rect {
    stroke: #000;
    stroke-width: 1;
}

/* Disable hover when selected - selection takes priority */
.box.selected:hover rect {
    stroke: #ff8040;
    stroke-width: 3;
}

/* Keep selected styling even when hovering over ports */
.box.selected:has(.port:hover) rect {
    stroke: #ff8040;
    stroke-width: 3;
}
```

**How it works:**
- `.box:has(.port:hover)` - Selects a box that contains a hovered port
- When hovering port → box returns to normal (black, 1px)
- If box is selected → orange persists even when hovering ports
- CSS `:has()` pseudo-class provides perfect isolation

### 2. JavaScript: Box Handler Ignores Port Clicks

**File:** `py2max/static/interactive.js` (lines 464-493)

```javascript
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
    this.dragStarted = false;

    const svgPoint = this.getSVGPoint(event);
    this.mouseDownPos = { x: svgPoint.x, y: svgPoint.y };

    this.dragOffset = {
        x: svgPoint.x - (box.x || 0),
        y: svgPoint.y - (box.y || 0)
    };

    this.selectedBox = box;
    this.selectedLine = null;

    this.render();
}
```

**How it works:**
- Check if `event.target` is a port
- If yes → return early, don't select box or start drag
- Allows port's click handler to execute without interference

### 3. JavaScript: Canvas Handler Preserves Port Interactions

**File:** `py2max/static/interactive.js` (lines 620-652)

```javascript
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
```

**How it works:**
- Check if clicking port → return early
- Prevents clearing `connectionStart` when clicking ports
- Allows connection creation to proceed normally

### 4. JavaScript: Add Selected Class for CSS Specificity

**File:** `py2max/static/interactive.js` (lines 193-201)

```javascript
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
```

**How it works:**
- Adds `selected` class when box is selected
- Enables CSS `.selected` rules to override hover states
- Increases stroke width to 3px for better visibility

## Event Flow

### Port Click Flow (Working)
```
1. Mousedown on port
   → handleBoxMouseDown() checks target → is port → returns early
   → Event bubbles to canvas
   → handleCanvasMouseDown() checks target → is port → returns early

2. Click on port
   → Port's click handler executes
   → Sets connectionStart or creates connection
   → render() highlights selected port
```

### Box Click Flow (Working)
```
1. Mousedown on box (not port)
   → handleBoxMouseDown() checks target → not port → continues
   → Sets selectedBox, prepares for drag
   → render() shows selection

2. Mousemove (if >5px)
   → Starts drag

3. Mouseup
   → If dragged: sends position update, clears selection
   → If not dragged: keeps selection visible
```

### Canvas Click Flow (Working)
```
1. Mousedown on empty canvas
   → handleCanvasMouseDown() checks target → not port/line → continues
   → Clears selections
   → Cancels pending connection
   → render() updates display
```

## Visual Hierarchy (CSS Specificity)

**Priority order (highest to lowest):**

1. **Selected + Port Hover** - `.box.selected:has(.port:hover) rect`
   - Specificity: 0-3-1
   - Orange outline, 3px width

2. **Selected + Hover** - `.box.selected:hover rect`
   - Specificity: 0-3-1
   - Orange outline, 3px width

3. **Port Hover** - `.box:has(.port:hover) rect`
   - Specificity: 0-2-1
   - Black outline, 1px width (normal state)

4. **Box Hover** - `.box:hover rect`
   - Specificity: 0-2-1
   - Blue outline, 2px width

5. **Normal** - `.box rect`
   - Specificity: 0-1-1
   - Black outline, 1px width

The specificity hierarchy ensures:
- Selection always visible (orange)
- Port hover doesn't trigger box hover (stays black)
- Box hover only when hovering box body (blue)

## User Experience

### Hovering Ports
✅ Port brightens (lighter blue for inlet, lighter orange for outlet)
✅ Box outline stays **normal** (black, 1px) - no blue
✅ Cursor changes to pointer
✅ Clear visual feedback: only port is interactive

### Clicking Ports for Connection
✅ First click → Port highlighted with yellow glow
✅ Info bar: "Connecting from [box] [type] [index]... Click [opposite type]"
✅ Second click → Connection created
✅ No box selection interference
✅ No canvas clearing interference

### Selecting Boxes
✅ Click box body → Orange outline appears **immediately**
✅ Orange persists during hover (no blue override)
✅ Can drag box after selection
✅ Delete key removes selected box

### Combined Interactions
✅ Selected box + hover port → Orange stays, port brightens
✅ Selected box + hover box → Orange stays (no blue)
✅ Port connection + box selection → Independent, no conflicts
✅ Click empty canvas → Deselects, cancels connections

## Browser Compatibility

**CSS `:has()` pseudo-class:**
- Chrome 105+ (August 2022)
- Firefox 121+ (December 2023)
- Safari 15.4+ (March 2022)
- Edge 105+ (September 2022)

Modern browsers fully supported. For older browsers, fallback would be JavaScript-based class toggling.

## Testing

### Manual Test
```bash
uv run python tests/examples/interactive_demo.py
# Open http://localhost:8765/interactive in browser
```

**Test scenarios:**
1. Hover port → Only port changes (box stays normal) ✅
2. Click port → Yellow highlight, connection starts ✅
3. Click second port → Connection created ✅
4. Click box → Orange selection appears ✅
5. Hover selected box → Orange persists ✅
6. Hover port on selected box → Orange + port brightens ✅
7. Click canvas → Deselects everything ✅

### Automated Tests
```bash
uv run pytest tests/
# 312 passed, 14 skipped in 11.42s
```

All tests pass with no regressions.

## Summary

Port interactions now work **perfectly** with complete separation from box interactions:

✅ **Visual Isolation** - Ports have independent hover states
✅ **Event Isolation** - Port clicks don't trigger box handlers
✅ **State Preservation** - Port connections not cancelled by canvas handler
✅ **Clear Hierarchy** - Selection > port > box hover
✅ **Max/MSP Parity** - Matches expected behavior

**Four-part solution:**
1. CSS `:has()` selector - Visual isolation
2. Box mousedown check - Prevent drag interference
3. Canvas mousedown check - Prevent connection cancellation
4. CSS specificity - Selection always visible

**Result:** Clean, intuitive port interactions with zero interference from box selection or hover states.
