# Interactive Save Feature

## Overview

The interactive editor now supports **manual save** with optional **auto-save** functionality. All web-based edits are persisted to the `.maxpat` file, ensuring Max/MSP can read the updated patch.

## Key Outcome

**When the web-based patch is saved, the state of the objects is reflected in the .maxpat JSON representation which Max/MSP can read.**

This is the critical feature that makes the interactive editor useful - changes made in the browser are written to the actual Max patch file.

## Features

### 1. Manual Save (Default)

- **Save Button**: Click the 💾 Save button in the web interface
- **Keyboard Shortcut**: Could be added (e.g., Ctrl+S / Cmd+S)
- **Visual Feedback**: Shows "Saving..." then "✅ Saved to [filepath]"
- **Error Handling**: Shows "❌ Save error: [message]" if save fails

### 2. Auto-Save (Optional)

- **Disabled by default** for safety and control
- **Debounced**: Waits 2 seconds after last edit before saving
- **Configurable**: Enable via `auto_save=True` parameter

## Usage

### Basic Usage (Manual Save Only)

```python
from py2max import Patcher

p = Patcher('demo.maxpat')
osc = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
p.add_line(osc, gain)
p.save()

# Start interactive server
await p.serve_interactive()  # auto_save=False by default

# Edit in browser, then click Save button to persist changes
```

### With Auto-Save Enabled

```python
from py2max import Patcher

p = Patcher('demo.maxpat')
osc = p.add_textbox('cycle~ 440')
p.save()

# Enable auto-save
await p.serve_interactive(auto_save=True)

# Edits automatically saved 2 seconds after last change
```

### Using serve_interactive Function

```python
from py2max import Patcher
from py2max.websocket_server import serve_interactive

p = Patcher('demo.maxpat')
p.add_textbox('cycle~ 440')
p.save()

# Manual save (default)
server = await serve_interactive(p, port=8000, auto_open=True, auto_save=False)

# Or with auto-save
server = await serve_interactive(p, port=8000, auto_open=True, auto_save=True)

# Server runs, edits are saved
await asyncio.sleep(60)
await server.shutdown()
```

## What Gets Saved

All interactive operations are saved to the `.maxpat` file:

### 1. Object Position Updates
```javascript
// Browser → Python
{ type: 'update_position', box_id: 'obj-123', x: 200, y: 150 }

// Python updates box.patching_rect
// Saves to .maxpat
```

### 2. Object Creation
```javascript
// Browser → Python
{ type: 'create_object', text: 'dac~', x: 300, y: 200 }

// Python creates box
// Saves to .maxpat
```

### 3. Connection Creation
```javascript
// Browser → Python
{
  type: 'create_connection',
  src_id: 'obj-123',
  dst_id: 'obj-456',
  src_outlet: 0,
  dst_inlet: 0
}

// Python creates patchline
// Saves to .maxpat
```

### 4. Object Deletion
```javascript
// Browser → Python
{ type: 'delete_object', box_id: 'obj-123' }

// Python removes box and orphaned connections
// Saves to .maxpat
```

### 5. Connection Deletion
```javascript
// Browser → Python
{
  type: 'delete_connection',
  src_id: 'obj-123',
  dst_id: 'obj-456',
  src_outlet: 0,
  dst_inlet: 0
}

// Python removes patchline
// Saves to .maxpat
```

## Save Flow

### Manual Save Flow

```
1. User edits patch in browser
   ↓
2. WebSocket sends edit message to Python
   ↓
3. Python updates Patcher state
   ↓
4. Python broadcasts updated state to all clients
   ↓
5. User clicks Save button
   ↓
6. Browser sends { type: 'save' } message
   ↓
7. Python calls patcher.save()
   ↓
8. .maxpat file updated on disk
   ↓
9. Python sends { type: 'save_complete', filepath: '...' }
   ↓
10. Browser shows "✅ Saved to [filepath]"
```

### Auto-Save Flow

```
1. User edits patch in browser
   ↓
2. WebSocket sends edit message to Python
   ↓
3. Python updates Patcher state
   ↓
4. Python broadcasts updated state to all clients
   ↓
5. Python calls schedule_save() (if auto_save=True)
   ↓
6. Python cancels previous save task (debounce)
   ↓
7. Python waits 2 seconds
   ↓
8. If no new edits, Python calls patcher.save()
   ↓
9. .maxpat file updated on disk
   ↓
10. Console: "Auto-saved: [filepath]"
```

## Max/MSP Roundtrip

The complete workflow ensures Max/MSP compatibility:

```python
# 1. Create patch in Python
p = Patcher('synth.maxpat')
osc = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
p.add_line(osc, gain)
p.save()

# 2. Edit in browser
await p.serve_interactive()
# User moves objects, adds dac~, creates connection
# User clicks Save button

# 3. Verify .maxpat file
import json
with open('synth.maxpat') as f:
    data = json.load(f)

# data['patcher']['boxes'] - Updated positions
# data['patcher']['lines'] - New connections

# 4. Load in Max/MSP
# File → Open → synth.maxpat
# All browser edits visible!

# 5. Reload in py2max
p2 = Patcher.from_file('synth.maxpat')
# All edits preserved
```

## Implementation Details

### Server-Side (Python)

**File**: `py2max/server.py`

**Key Components**:

1. **InteractiveWebSocketHandler.__init__**:
   ```python
   def __init__(self, patcher, auto_save=False):
       self.auto_save = auto_save
       self._save_task = None
   ```

2. **handle_save()** - Manual save handler:
   ```python
   async def handle_save(self):
       if self.patcher and self.patcher.filepath:
           self.patcher.save()
           await self.broadcast({
               'type': 'save_complete',
               'filepath': str(self.patcher.filepath)
           })
   ```

3. **schedule_save()** - Auto-save scheduler:
   ```python
   async def schedule_save(self):
       if not self.auto_save:
           return  # Disabled by default

       # Cancel previous task (debounce)
       if self._save_task and not self._save_task.done():
           self._save_task.cancel()

       # Schedule new save
       self._save_task = asyncio.create_task(self._debounced_save())
   ```

4. **_debounced_save()** - Delayed save:
   ```python
   async def _debounced_save(self):
       try:
           await asyncio.sleep(2.0)  # 2 second delay
           if self.patcher and self.patcher.filepath:
               self.patcher.save()
               print(f"Auto-saved: {self.patcher.filepath}")
       except asyncio.CancelledError:
           pass  # Cancelled by new edit
   ```

### Client-Side (JavaScript)

**File**: `py2max/static/interactive.js`

**Key Components**:

1. **Save Button Handler**:
   ```javascript
   initializeControls() {
       const saveBtn = document.getElementById('save-btn');
       saveBtn.addEventListener('click', () => {
           this.handleSave();
       });
   }
   ```

2. **handleSave()** - Send save request:
   ```javascript
   handleSave() {
       this.sendMessage({ type: 'save' });
       this.updateInfo('Saving...');
   }
   ```

3. **handleUpdate()** - Process save responses:
   ```javascript
   handleUpdate(data) {
       if (data.type === 'save_complete') {
           this.updateInfo(`✅ Saved to ${data.filepath}`);
       } else if (data.type === 'save_error') {
           this.updateInfo(`❌ Save error: ${data.message}`);
       }
   }
   ```

**File**: `py2max/static/interactive.html`

```html
<button id="save-btn" title="Save patch to .maxpat file">💾 Save</button>
```

## Auto-Save vs Manual Save

### Manual Save (Recommended)

**Pros**:
- ✅ User has full control
- ✅ No accidental saves
- ✅ Can review changes before saving
- ✅ Clear when file is modified vs saved

**Cons**:
- ❌ User must remember to save
- ❌ Could lose work if browser crashes

**Best for**:
- Careful editing
- Experimental changes
- Teaching/demonstrations

### Auto-Save

**Pros**:
- ✅ Never lose work
- ✅ Automatic persistence
- ✅ Good for rapid prototyping

**Cons**:
- ❌ No undo (saves everything)
- ❌ Could save unwanted changes
- ❌ Frequent disk writes

**Best for**:
- Long editing sessions
- Rapid prototyping
- Collaborative editing

## Testing

Run the WebSocket tests:

```bash
uv run pytest tests/test_websocket.py -v
```

Manual testing:

```bash
uv run python tests/examples/interactive_demo.py
```

Test workflow:
1. Open browser to http://localhost:8000/
2. Move an object
3. Click Save button
4. Check console: "Saved: [filepath]"
5. Verify .maxpat file updated
6. Reload in Max/MSP - changes visible

## Error Handling

### No Filepath Set

```python
p = Patcher()  # No filepath!
await p.serve_interactive()

# Click Save → Error message
# Browser shows: "❌ Save error: No filepath set"
```

### File Permission Error

```python
p = Patcher('/readonly/path.maxpat')
await p.serve_interactive()

# Click Save → Error message
# Browser shows: "❌ Save error: Permission denied"
```

### WebSocket Disconnected

```javascript
// Browser detects disconnect
this.updateStatus('Disconnected', 'disconnected');

// Save button disabled or shows error
// Auto-reconnect after 3 seconds
```

## Summary

The interactive editor now provides **complete persistence**:

✅ **Manual save** - User clicks button to save (default)
✅ **Auto-save** - Optional 2-second debounced save
✅ **Visual feedback** - Shows save status in info bar
✅ **Error handling** - Clear error messages
✅ **Max/MSP compatible** - Saves to standard .maxpat format
✅ **All operations** - Position, create, delete, connect
✅ **Debouncing** - Prevents excessive saves during drag
✅ **Configurable** - Enable/disable auto-save as needed

**Key outcome achieved**: Web-based patch edits are persisted to .maxpat files that Max/MSP can read!
