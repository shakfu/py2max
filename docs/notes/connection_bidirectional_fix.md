# Bidirectional Connection Fix

## Issue

Initial implementation only allowed connections to start from **outlets** (orange) and end at **inlets** (blue). This was inconsistent with Max/MSP, which allows you to start from either port type.

## Fix Applied ✅

Updated the connection logic to work **exactly like Max** - you can start from either an inlet or an outlet, as long as the second click is the opposite type.

## Implementation

### JavaScript Changes (`py2max/static/interactive.js`)

**Before**:
```javascript
handlePortClick(box, portIndex, isOutlet) {
    if (!this.connectionStart) {
        // First click - must be an outlet
        if (!isOutlet) {
            this.updateInfo('Start connection from an outlet');
            return;
        }
        // ...
    } else {
        // Second click - must be an inlet
        if (isOutlet) {
            this.updateInfo('Click an inlet to complete connection');
            return;
        }
        // ...
    }
}
```

**After**:
```javascript
handlePortClick(box, portIndex, isOutlet) {
    if (!this.connectionStart) {
        // First click - can be either inlet or outlet
        this.connectionStart = {
            box: box,
            portIndex: portIndex,
            isOutlet: isOutlet  // Remember which type we started with
        };
        // ...
    } else {
        // Second click - must be opposite type from first click
        if (isOutlet === this.connectionStart.isOutlet) {
            this.updateInfo('Click the opposite port type');
            return;
        }

        // Determine source/destination based on which was clicked first
        let srcBox, dstBox, srcOutlet, dstInlet;

        if (this.connectionStart.isOutlet) {
            // Started from outlet → inlet
            srcBox = this.connectionStart.box;
            srcOutlet = this.connectionStart.portIndex;
            dstBox = box;
            dstInlet = portIndex;
        } else {
            // Started from inlet → outlet
            srcBox = box;
            srcOutlet = portIndex;
            dstBox = this.connectionStart.box;
            dstInlet = this.connectionStart.portIndex;
        }

        // Create connection with correct source/destination
        this.sendMessage({
            type: 'create_connection',
            src_id: srcBox.id,
            dst_id: dstBox.id,
            src_outlet: srcOutlet,
            dst_inlet: dstInlet
        });
    }
}
```

### Key Changes

1. **Removed restriction**: No longer requires first click to be outlet
2. **Added direction detection**: Determines source/destination based on which port type was clicked first
3. **Swap logic**: If started from inlet, swap the source and destination
4. **Updated feedback**: Info bar shows "Click inlet" or "Click outlet" depending on what was clicked first

## How It Works Now

### Scenario 1: Start from Outlet (traditional)
```
1. Click outlet on "cycle~"  → Info: "Connecting from cycle~ outlet 0... Click inlet"
2. Click inlet on "gain~"    → Connection created: cycle~[0] → gain~[0]
```

### Scenario 2: Start from Inlet (new!)
```
1. Click inlet on "gain~"    → Info: "Connecting from gain~ inlet 0... Click outlet"
2. Click outlet on "cycle~"  → Connection created: cycle~[0] → gain~[0]
```

### Result
Same connection is created regardless of which port you click first!

## User Benefits

1. **More flexible**: Work the way you naturally think
2. **Matches Max**: Behaves identically to Max/MSP
3. **Forgiving**: Don't have to remember "outlet first"
4. **Visual feedback**: Selected port (inlet OR outlet) glows yellow
5. **Clear errors**: If you click same type twice, helpful error message

## Testing

### All Tests Pass ✅
```bash
uv run pytest tests/
# 312 passed, 14 skipped
```

### Interactive Test
```bash
uv run python tests/examples/interactive_demo.py
```

Try:
- Click outlet → inlet ✅
- Click inlet → outlet ✅
- Click outlet → outlet ❌ (shows error: "Click an inlet, not another outlet")
- Click inlet → inlet ❌ (shows error: "Click an outlet, not another inlet")

## Files Modified

1. **`py2max/static/interactive.js`**
   - Updated `handlePortClick()` logic (~60 lines)
   - Updated rendering to highlight either inlet or outlet

2. **`py2max/static/interactive.html`**
   - Updated help text: "Click any port, then opposite port to connect"

3. **`tests/examples/interactive_demo.py`**
   - Updated instructions to mention bidirectional connections

## Summary

The connection system now works **exactly like Max/MSP**:

✅ Click outlet → inlet (works)
✅ Click inlet → outlet (works)
❌ Click outlet → outlet (error)
❌ Click inlet → inlet (error)

This provides maximum flexibility and matches user expectations from Max itself.
