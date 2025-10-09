# Save Filepath Fix

## Issue

When clicking the Save button, the error "No filepath set" appeared even though the patcher had a filepath. The issue was that the patcher needed to be **saved initially** before the interactive server could save subsequent changes.

## Root Cause

The interactive demo created a patcher with a filepath but never called `p.save()` initially:

```python
p = Patcher('interactive_demo.maxpat')  # Has filepath
osc = p.add_textbox('cycle~ 440')
# ... but p.save() was never called!

await p.serve_interactive()  # Server starts but file doesn't exist yet
```

## Solution

### 1. Save Initial Patch

Always save the patcher before starting the interactive server:

```python
p = Patcher('interactive_demo.maxpat')
osc = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
p.add_line(osc, gain)

# Save initial patch
p.save()  # ← Important!

# Now server can save updates
await p.serve_interactive()
```

### 2. Show Filepath in UI

Added filepath to the state JSON so the Save button can show which file will be saved:

**Server (`py2max/server.py:117`)**:
```python
return {
    'type': 'update',
    'boxes': boxes,
    'lines': lines,
    'title': getattr(patcher, 'title', 'Untitled Patch'),
    'filepath': str(getattr(patcher, 'filepath', '')) if hasattr(patcher, 'filepath') else '',
}
```

**Client (`py2max/static/interactive.js:147-151`)**:
```javascript
// Update save button tooltip with filepath
if (data.filepath) {
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.title = `Save patch to ${data.filepath}`;
    }
}
```

Now hovering over the Save button shows: **"Save patch to interactive_demo.maxpat"**

## Updated Demo

**File**: `tests/examples/interactive_demo.py`

```python
# Optimize layout
p.optimize_layout()

# Save initial patch (ADDED)
p.save()
print(f"Saved initial patch: {p.filepath}")

# Start interactive server
await p.serve_interactive()
```

**Updated instructions**:
```
6. Click the 💾 Save button to save changes to .maxpat file
```

## Testing

Run the demo:
```bash
uv run python tests/examples/interactive_demo.py
```

Verify:
1. ✅ Console shows: "Saved initial patch: interactive_demo.maxpat"
2. ✅ Hover over Save button → Shows filepath in tooltip
3. ✅ Click Save button → "✅ Saved to interactive_demo.maxpat"
4. ✅ No "No filepath set" error

## Best Practice

**Always save the patcher before starting the interactive server:**

```python
from py2max import Patcher

# Good ✅
p = Patcher('myfile.maxpat')
p.add_textbox('cycle~ 440')
p.save()  # Save initial version
await p.serve_interactive()

# Bad ❌
p = Patcher('myfile.maxpat')
p.add_textbox('cycle~ 440')
await p.serve_interactive()  # File doesn't exist yet!
```

Or use a temporary file for prototyping:

```python
import tempfile
from pathlib import Path

with tempfile.NamedTemporaryFile(mode='w', suffix='.maxpat', delete=False) as f:
    temp_path = Path(f.name)

p = Patcher(str(temp_path))
p.add_textbox('cycle~ 440')
p.save()  # Create the file
await p.serve_interactive()

# Cleanup when done
temp_path.unlink()
```

## Summary

The save functionality now works correctly:

✅ Demo saves initial patch before starting server
✅ Save button tooltip shows filepath
✅ No "No filepath set" error
✅ Clear visual feedback on save success
✅ Best practices documented

**Key lesson**: Always call `patcher.save()` before starting the interactive server to ensure the file exists and can be saved to.
