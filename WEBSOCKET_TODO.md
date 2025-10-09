# WebSocket Interactive Editor - Known Issues & TODO

## Known Issues to Fix

### 1. Connection Mode Not Working
**Problem**: The "Connect" button mode is not functioning correctly in the browser.

**Likely Causes**:
- Event handler conflicts between drag mode and connection mode
- WebSocket message not being sent/received correctly
- Port selection logic for outlets/inlets needs refinement

**To Debug**:
- Check browser console for JavaScript errors
- Verify WebSocket messages are being sent when clicking in connection mode
- Test the `handleBoxClick` event handler

### 2. Saving Repositioned Objects
**Problem**: When objects are dragged in the browser, positions update in Python memory but may not persist to the .maxpat file.

**Solution Needed**:
- Add auto-save option after position updates
- Or add a "Save" button in the browser UI
- Or call `p.save()` in the position update handler

**Implementation Options**:

```python
# Option 1: Auto-save on every update
async def handle_update_position(self, data: dict):
    # ... update position ...
    if self.patcher and hasattr(self.patcher, 'filepath'):
        self.patcher.save()  # Auto-save
    await self.broadcast(state)

# Option 2: Debounced save (better for performance)
# Save only after 2 seconds of no movement
self.save_timer = None

async def handle_update_position(self, data: dict):
    # ... update position ...

    # Cancel previous save timer
    if self.save_timer:
        self.save_timer.cancel()

    # Schedule save after 2 seconds
    self.save_timer = asyncio.create_task(self.debounced_save())

async def debounced_save(self):
    await asyncio.sleep(2)
    if self.patcher:
        self.patcher.save()
        print("Auto-saved patch")
```

## Testing Checklist

When resuming work:
- [ ] Test connection mode thoroughly
- [ ] Add browser console logging for debugging
- [ ] Verify WebSocket messages for connections
- [ ] Test save functionality after drag-and-drop
- [ ] Add UI feedback for save operations
- [ ] Test with multiple simultaneous clients

## Enhancement Ideas (Future)

- [ ] Add undo/redo functionality
- [ ] Add "Save" button in browser UI with visual feedback
- [ ] Add keyboard shortcuts (Delete key, Ctrl+S for save, etc.)
- [ ] Show connection preview line while in connection mode
- [ ] Add hover states for outlets/inlets
- [ ] Add visual feedback when creating connections
- [ ] Add ability to delete connections by clicking them
- [ ] Add object selection (click to select, shift-click for multi-select)
- [ ] Add copy/paste functionality

## Current Status

✅ **Working**:
- WebSocket server with bidirectional communication
- HTTP server serving static files
- Drag-and-drop object repositioning
- Real-time sync Python ↔ Browser
- All 312 tests passing
- Context manager support

❌ **Not Working**:
- Connection mode (button toggles but connections not created)
- Auto-save of repositioned objects

⚠️ **Needs Testing**:
- Multiple simultaneous browser clients
- Large patches with many objects
- Network latency handling
- Error recovery

## Next Session Plan

1. Fix connection mode:
   - Debug JavaScript event handlers
   - Add console logging
   - Test WebSocket message flow

2. Implement save functionality:
   - Add debounced auto-save
   - Add "Save" button to UI
   - Add save status indicator

3. Polish UI:
   - Add better visual feedback
   - Add keyboard shortcuts
   - Improve connection mode UX

4. Test thoroughly:
   - Test all interactive features
   - Test with multiple clients
   - Document any edge cases

## Good Night! 😴

Great work implementing the WebSocket server and interactive editor. The foundation is solid - just needs a couple of bug fixes and we'll have a fully functional interactive patch editor!
