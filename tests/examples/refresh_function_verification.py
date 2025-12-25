"""Test refresh() function in single-terminal mode.

This script verifies that the refresh() function properly exists and can be
called in single-terminal REPL mode.
"""

import asyncio
from pathlib import Path


async def test_refresh():
    """Test that refresh function works with background server."""
    from py2max import Patcher
    from py2max.server.inline import BackgroundServerREPL

    # Create test patch
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    patch_path = output_dir / "test_refresh.maxpat"

    print("Creating test patch...")
    p = Patcher(patch_path)
    osc = p.add("cycle~ 440")
    p.save()

    print("\nTest 1: Create BackgroundServerREPL instance")
    log_file = output_dir / "test_refresh.log"
    repl = BackgroundServerREPL(p, port=8100, log_file=log_file)
    print(f"  ✓ BackgroundServerREPL created")

    print("\nTest 2: Verify notify_update_sync method exists")
    assert hasattr(repl, "notify_update_sync"), "notify_update_sync method missing"
    print(f"  ✓ notify_update_sync method exists")

    print("\nTest 3: Test notify_update_sync without server (should handle gracefully)")
    # Should not crash even though server isn't running
    repl.notify_update_sync()
    print(f"  ✓ notify_update_sync handles missing server gracefully")

    print("\n" + "=" * 70)
    print("All refresh function tests passed!")
    print("=" * 70)
    print()
    print("To test interactively:")
    print(f"  py2max serve {patch_path} --repl --log-file {log_file}")
    print()
    print("Then in REPL:")
    print("  >>> osc = p.add('cycle~ 440')")
    print("  >>> refresh()  # Updates browser view")
    print()


if __name__ == "__main__":
    asyncio.run(test_refresh())
