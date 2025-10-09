# Immediate Selection Feedback

## Issue

There was a noticeable delay between clicking an object and seeing the orange selection outline appear. The selection only appeared on `mouseup`, not `mousedown`.

## Cause

The selection highlight was only rendered in `handleCanvasMouseUp()` (after determining if it was a click vs drag):

**Previous flow:**
1. `mousedown` → Set `selectedBox`, but don't render
2. `mousemove` → Check if drag started (>5px threshold)
3. `mouseup` → If no drag, render selection ← **Delay here**

Users had to wait until releasing the mouse to see the selection feedback.

## Solution

Added `this.render()` call immediately in `handleBoxMouseDown()`:

```javascript
handleBoxMouseDown(event, box) {
    event.stopPropagation();

    // ... drag preparation code ...

    // Store which box for potential drag or selection
    this.selectedBox = box;
    this.selectedLine = null;

    // Show selection immediately (before drag starts)
    this.render();  // ← Added this line
}
```

## How It Works Now

### Immediate Feedback Flow:

1. **Mouse down** → Select box, render immediately → **Orange border appears instantly**
2. **Mouse move** (if >5px) → Start dragging
3. **Mouse up**:
   - If dragged: Send update, clear selection
   - If clicked: Keep selection (already visible)

### User Experience:

**Before (delayed):**
```
Click down → (wait) → Release → Orange border appears
         └─ Noticeable delay ─┘
```

**After (instant):**
```
Click down → Orange border appears immediately!
```

## Benefits

1. **Instant feedback** - Visual response on mousedown
2. **Feels responsive** - No perceived lag
3. **Clear intent** - User knows selection worked immediately
4. **Natural feel** - Matches OS and other app behavior

## Edge Cases

### What if user starts dragging?

The selection is shown immediately on mousedown, but if drag starts (>5px movement):
- Object moves with selection visible
- On mouseup: Selection cleared after position update
- Result: Selection briefly visible during drag, which is fine

### What if click is canceled?

If user clicks empty canvas or another object:
- Previous selection cleared
- New selection shown
- Works as expected

### Multiple rapid clicks?

Each click:
- Shows selection immediately
- Switches selection to new object
- Previous selection cleared
- No issues, works smoothly

## Testing

### Manual Test:
```bash
uv run python tests/examples/interactive_demo.py
```

**Test instant feedback:**
1. Click an object → Orange border appears **immediately**
2. Release mouse → Border stays (selected)
3. Click and drag >5px → Object moves
4. Release → Selection cleared (was a drag)

### Performance Impact:

**Added one `render()` call per mousedown.**

Impact: Minimal
- Render is already fast
- Only affects clicks/drags on objects
- No performance degradation noticed

### All Tests Pass ✅:
```bash
uv run pytest tests/
# 312 passed, 14 skipped in 11.48s
```

## Comparison to Max/MSP

| Action | Max/MSP | py2max (before) | py2max (after) |
|--------|---------|-----------------|----------------|
| Click object | Immediate border | Delayed until mouseup | **Immediate border** ✅ |
| Drag object | Border during drag | No border until release | **Border appears** ✅ |
| Release after drag | No border | No border | **No border** ✅ |

Now matches Max/MSP's instant visual feedback!

## Code Changes

**File:** `py2max/static/interactive.js`

**Lines changed:** 1 line added (line 483)

```diff
    handleBoxMouseDown(event, box) {
        // ... existing code ...

        this.selectedBox = box;
        this.selectedLine = null;
+       this.render();  // Show selection immediately
    }
```

## Summary

Selection feedback is now **instant**:

✅ Orange border appears on `mousedown` (not `mouseup`)
✅ No noticeable delay
✅ Feels responsive and snappy
✅ Matches expected behavior from Max/MSP
✅ All tests pass
✅ No performance impact

Simple one-line fix that significantly improves perceived responsiveness!
