# Hover/Selection Visual Feedback Fix

## Issue

When an object was selected, the blue hover outline was covering the orange selection outline, making it appear as if the selection didn't happen until the mouse moved away.

**User observation:** "When you hover over an object it develops blue outline to indicate that it in focus. When you select an object, its outline is still blue as per the focus features, until the pointer moves away and then it shows that it has an orange outline (that it is selected)."

## Root Cause

CSS specificity issue where the hover state (`.box:hover rect`) was taking precedence over the selection state styling. The selection highlight was being set via JavaScript attribute manipulation (`rect.setAttribute('stroke', '#ff8040')`), but the CSS hover rule was overriding it.

## Solution

Added CSS rule to ensure selected objects maintain their orange outline even when hovered, and added a `selected` class to the box element when selected.

### Implementation

**1. Added CSS override rule** (`interactive.html:132-135`):

```css
/* Disable hover when selected - selection takes priority */
.box.selected:hover rect {
    stroke: #ff8040;
    stroke-width: 3;
}
```

This rule has higher specificity than `.box:hover rect` because it includes the `.selected` class, ensuring the orange selection color persists even when hovering.

**2. Added selected class in JavaScript** (`interactive.js:195`):

```javascript
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
```

Also increased selection stroke width from `2` to `3` for better visual distinction.

## How It Works Now

### Selection Flow

1. **Mouse down on object** → Object selected
2. `render()` called → Adds `selected` class to box element
3. **Hover state** → CSS rule `.box.selected:hover rect` applies (orange, not blue)
4. **Visual feedback** → Orange outline visible immediately, even while hovering

### User Experience

**Before (confusing):**

```text
1. Click object → Blue outline (hover state)
2. Hold click → Still blue
3. Move mouse away → Orange appears (finally shows selection)
   └─ Confusing - looked like selection didn't work
```

**After (clear):**

```text
1. Click object → Orange outline appears immediately!
2. Hold click → Stays orange
3. Move mouse → Still orange (selected state maintained)
   └─ Clear feedback - user knows selection worked
```

## CSS Specificity Details

**Specificity hierarchy:**

1. `.box:hover rect` - specificity: 0-2-1 (1 class + 1 pseudo-class + 1 element)
2. `.box.selected:hover rect` - specificity: 0-3-1 (2 classes + 1 pseudo-class + 1 element)

The selected rule wins because it has higher specificity (3 classes/pseudo-classes vs 2).

## Visual States

**Normal (unselected, not hovering):**

- Stroke: black (`#000`)
- Stroke width: 1px

**Hover (unselected):**

- Stroke: blue (`#4080ff`)
- Stroke width: 2px

**Selected:**

- Stroke: orange (`#ff8040`)
- Stroke width: 3px
- Maintains orange even when hovering

**Selected + Hovering:**

- Stroke: orange (`#ff8040`) - maintained!
- Stroke width: 3px
- No blue outline interference

## Testing

### Manual Test

```bash
uv run python tests/examples/interactive_demo.py
```

**Test instant selection feedback:**

1. Hover over object → Blue outline appears
2. Click object → **Orange outline appears immediately** (not blue!)
3. Keep mouse on object → Orange stays (doesn't revert to blue)
4. Move mouse away → Orange persists (object still selected)
5. Click empty canvas → Deselects, orange disappears

### Edge Cases

1. **Rapid click-hover**: Orange appears instantly, no blue flash
2. **Click and hold**: Orange stays visible throughout
3. **Drag object**: Orange visible during drag
4. **Multiple rapid selections**: Each shows orange immediately

## Port Click Interference Fix

After the initial fix, there was a secondary issue: **port clicks were being intercepted by the box mousedown handler**, preventing inlet/outlet connections from being created.

### Problem

When clicking a port (inlet/outlet):

1. **Mousedown** event fires on port → bubbles to box → `handleBoxMouseDown()` runs
2. Box gets selected and `render()` is called
3. **Click** event fires on port → `handlePortClick()` runs
4. But box selection interfered with connection creation

### Solution

Added check in `handleBoxMouseDown()` to ignore mousedown events on ports:

```javascript
handleBoxMouseDown(event, box) {
    // Don't handle if clicking on a port - let port handler deal with it
    if (event.target.classList.contains('port') ||
        event.target.classList.contains('inlet') ||
        event.target.classList.contains('outlet')) {
        return;
    }
    // ... rest of handler
}
```

This ensures port clicks are handled exclusively by the port click handlers, not the box drag/selection handler.

## Port Hover Interference Fix

A third issue emerged: **when hovering over ports (inlets/outlets), the box would show a blue outline** as if the entire box was being hovered. This was confusing because the user was trying to interact with the port, not the box.

### Problem

The CSS rule `.box:hover rect` was applying whenever the mouse was over any child element of the box, including ports. Since ports are children of the box SVG group, hovering over a port triggered the box hover state.

### Solution

Used the CSS `:has()` pseudo-class to disable box hover styling when hovering over ports:

```css
/* Disable box hover when hovering over ports - ports have their own hover */
.box:has(.port:hover) rect {
    stroke: #000;
    stroke-width: 1;
}

/* Keep selected styling even when hovering over ports */
.box.selected:has(.port:hover) rect {
    stroke: #ff8040;
    stroke-width: 3;
}
```

### How it works

- `.box:has(.port:hover)` - Selects a box that contains a hovered port
- When hovering a port, box outline returns to normal (black, 1px)
- Ports have their own hover effects (lighter color, thicker stroke)
- If box is selected, orange outline persists even when hovering ports

This creates clear visual separation: **port hover affects only the port**, not the entire box.

## Port Selection Fix (Canvas Mousedown Interference)

A fourth issue was discovered: **port clicks weren't registering for connections**. When you clicked a port to start a connection, nothing happened.

### Problem

The event flow was:

1. **Mousedown** on port → `handleBoxMouseDown()` returns early → event bubbles to canvas
2. **Canvas mousedown handler** runs → clears `this.connectionStart = null` (line 636)
3. **Click** on port → `handlePortClick()` runs, but `connectionStart` already cleared!

The canvas mousedown handler was canceling pending connections before the port click handler could execute.

### Solution

Added port check to `handleCanvasMouseDown()` to prevent it from clearing connection state when clicking ports:

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

    // ... rest of handler (deselect, cancel connection)
}
```

Now when clicking a port, **both** `handleBoxMouseDown()` and `handleCanvasMouseDown()` return early, allowing the port's click handler to work without interference.

## Files Modified

**`py2max/static/interactive.html`**:

- Added CSS rule for `.box.selected:hover rect` (lines 138-141) - Selection overrides hover
- Added CSS rule for `.box:has(.port:hover) rect` (lines 132-135) - Disable box hover when hovering ports
- Added CSS rule for `.box.selected:has(.port:hover) rect` (lines 144-147) - Keep selection visible when hovering ports
- Ensures proper visual hierarchy: selection > port hover > box hover

**`py2max/static/interactive.js`**:

- Added `boxEl.classList.add('selected')` when rendering selected boxes (line 195)
- Increased selection stroke width from 2 to 3 (line 199)
- **Added port click check** in `handleBoxMouseDown()` (lines 465-470) - Prevents box drag handler from interfering
- **Added port click check** in `handleCanvasMouseDown()` (lines 623-628) - Prevents connection cancellation
- Ensures selected class is applied for CSS specificity
- Prevents both box and canvas handlers from interfering with port clicks

## Benefits

1. **Immediate visual feedback** - Orange outline appears on mousedown
2. **Clear selection state** - No confusion about whether selection worked
3. **Consistent behavior** - Selection color persists during hover
4. **Better UX** - Matches expected behavior from desktop applications
5. **No delay perception** - User sees instant response

## Visual Hierarchy

The complete CSS specificity hierarchy ensures proper visual feedback:

1. **Port hover** (highest priority for ports)
   - Ports have their own hover effects
   - Box hover disabled when hovering ports (`:has(.port:hover)`)

2. **Box selection** (highest priority for boxes)
   - Orange outline (3px)
   - Persists even when hovering (`.selected:hover`)
   - Persists even when hovering ports (`.selected:has(.port:hover)`)

3. **Box hover** (normal state)
   - Blue outline (2px)
   - Only when hovering box body (not ports)

4. **Normal** (default state)
   - Black outline (1px)

## Summary

Visual feedback is now **crystal clear** with proper separation of concerns:

[x] **Object selection** - Orange outline appears instantly on mousedown
[x] **Object hover** - Blue outline only when hovering box body (not ports)
[x] **Port hover** - Only port changes appearance, box stays normal
[x] **Port clicks work** - No interference from box mousedown handler
[x] **Selection persists** - Orange visible even when hovering or hovering ports
[x] **Clear visual hierarchy** - Selection > port interaction > box hover > normal

Four-part fix that creates perfect visual separation:

1. **CSS `:has()` selector** - Disable box hover when hovering ports
2. **CSS specificity** - Selection overrides all hover states
3. **Event target check in `handleBoxMouseDown()`** - Box drag handler ignores port clicks
4. **Event target check in `handleCanvasMouseDown()`** - Canvas handler doesn't cancel connections on port clicks

All visual feedback and interaction issues are now resolved! [x]
