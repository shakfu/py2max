# Orphaned Connection Handling

## Overview

When an object is deleted, **all connections to and from that object are automatically removed**. This matches Max/MSP's behavior and prevents orphaned connections.

## Implementation

### Server-Side Logic (`py2max/websocket_server.py`)

When `handle_delete_object()` is called:

```python
async def handle_delete_object(self, data: dict):
    """Handle object deletion from browser."""
    box_id = data.get('box_id')

    # Find and remove box
    for i, box in enumerate(self.patcher._boxes):
        if box.id == box_id:
            self.patcher._boxes.pop(i)

            # Also remove any connected lines
            self.patcher._lines = [
                line for line in self.patcher._lines
                if line.src != box_id and line.dst != box_id
            ]

            # Broadcast update to all clients
            await self.broadcast(state)
            break
```

**Key Logic** (lines 276-279):
- Filters out any line where `src == box_id` (outgoing connections)
- Filters out any line where `dst == box_id` (incoming connections)
- Result: All connections involving the deleted object are removed

## Examples

### Example 1: Delete Middle Object

**Before deletion:**
```
cycle~ → gain~ → dac~
```

**Delete gain~:**
- Object removed: `gain~`
- Connections removed:
  - `cycle~ → gain~` (incoming)
  - `gain~ → dac~` (outgoing)

**After deletion:**
```
cycle~    dac~
(no connections)
```

### Example 2: Delete Source Object

**Before deletion:**
```
metro → random → print
```

**Delete metro:**
- Object removed: `metro`
- Connections removed:
  - `metro → random` (outgoing)

**After deletion:**
```
random → print
(one connection remains)
```

### Example 3: Object with Multiple Connections

**Before deletion:**
```
    ┌─→ osc1
metro─┼─→ osc2
    └─→ osc3
```

**Delete metro:**
- Object removed: `metro`
- Connections removed:
  - `metro → osc1` (outgoing)
  - `metro → osc2` (outgoing)
  - `metro → osc3` (outgoing)

**After deletion:**
```
osc1
osc2
osc3
(no connections)
```

## Browser Behavior

When you delete an object in the browser:

1. **Click object** → Selected (orange border)
2. **Press Delete** → `delete_object` message sent to server
3. **Server processes**:
   - Removes object from `_boxes`
   - Removes all related connections from `_lines`
4. **Broadcast update** → All clients re-render
5. **Browser receives update** → Object AND its connections disappear

The user sees all connections vanish simultaneously with the object, just like in Max.

## Visual Feedback

- **Selected object** turns orange
- **Press Delete** → Object disappears
- **All connected lines** disappear at the same time
- **Smooth transition** - no orphaned dangling connections

## Testing

### Automated Test

The logic is tested in `tests/test_websocket.py`:

```python
def test_handle_delete_object():
    # Create connected objects
    p.add_line(box1, box2)

    # Delete box1
    await handler.handle_delete_object({'box_id': box1.id})

    # Verify connections are removed
    assert len(p._lines) == 0
```

### Manual Test

```bash
uv run python tests/examples/interactive_demo.py
```

1. **Open browser** - see connected objects
2. **Click middle object** (e.g., "random")
3. **Press Delete**
4. **Observe**: Object AND both connections disappear together

### Verification Test

```python
# Create chain: osc → gain → dac
osc = p.add_textbox('cycle~ 440')
gain = p.add_textbox('gain~')
dac = p.add_textbox('ezdac~')
p.add_line(osc, gain)
p.add_line(gain, dac)

print(f'Before: {len(p._boxes)} boxes, {len(p._lines)} lines')
# Before: 3 boxes, 2 lines

# Delete middle object
await handler.handle_delete_object({'box_id': gain.id})

print(f'After: {len(p._boxes)} boxes, {len(p._lines)} lines')
# After: 2 boxes, 0 lines

# ✓ Both connections removed automatically!
```

## Comparison to Max/MSP

| Scenario | Max/MSP | py2max Interactive |
|----------|---------|-------------------|
| Delete connected object | Removes object + connections | ✅ Same behavior |
| Visual feedback | Instant disappearance | ✅ Same behavior |
| Orphaned connections | Never created | ✅ Never created |
| Undo capability | Can undo deletion | ❌ Not yet implemented |

## Edge Cases Handled

### 1. Object with No Connections
```python
# Object has no connections
await handler.handle_delete_object({'box_id': isolated_box.id})
# Result: Only object removed, no connections to clean up
```

### 2. Object with Only Incoming Connections
```python
# metro → box (box has 1 incoming, 0 outgoing)
await handler.handle_delete_object({'box_id': box.id})
# Result: Object + incoming connection removed
```

### 3. Object with Only Outgoing Connections
```python
# box → print (box has 0 incoming, 1 outgoing)
await handler.handle_delete_object({'box_id': box.id})
# Result: Object + outgoing connection removed
```

### 4. Hub Object (Many Connections)
```python
# Multiple objects connected to/from hub
await handler.handle_delete_object({'box_id': hub.id})
# Result: Hub + ALL connections removed (both directions)
```

## Implementation Notes

### Why This Works

The connection removal uses a **list comprehension** that:
1. Iterates through all connections
2. Keeps only those where NEITHER endpoint is the deleted object
3. Replaces the entire `_lines` list

This is **O(n)** where n = number of connections, which is efficient.

### Alternative Approaches Considered

**Approach 1: Individual removal (rejected)**
```python
# Slower - multiple list operations
for line in list(patcher._lines):
    if line.src == box_id or line.dst == box_id:
        patcher._lines.remove(line)
```

**Approach 2: Filter in place (rejected)**
```python
# More complex, no performance benefit
patcher._lines[:] = filter(lambda line: ..., patcher._lines)
```

**Current approach (chosen)**:
- Simple and clear
- Single pass through connections
- Creates new list (avoids modification-during-iteration)
- Easy to understand and maintain

## Summary

Orphaned connection handling is **fully implemented and tested**:

- ✅ Deleting an object removes ALL connections to/from it
- ✅ Works for incoming, outgoing, and bidirectional connections
- ✅ Happens atomically (all at once)
- ✅ Visual feedback matches Max/MSP
- ✅ No orphaned dangling connections ever created
- ✅ Efficient O(n) implementation
- ✅ All tests pass

Users can confidently delete objects knowing that the patch will remain clean with no orphaned connections.
