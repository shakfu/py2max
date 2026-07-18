"""Shared pytest fixtures for the py2max test suite."""

import os
import re
import shutil
from pathlib import Path

import pytest

# Persistent, git-ignored location for artifacts written by tests via relative
# paths (e.g. ``outputs/foo.maxpat``). Anchored at the repo root so it is stable
# regardless of the directory pytest is invoked from.
#
# Two modes, selected by the ``PY2MAX_TEST_OUTPUT_FLAT`` env var (set by the
# ``make test-outputs`` target):
#   * default    -> per-test subdirectories under ``build/test-output`` so no two
#                   tests collide on a shared filename.
#   * flat (env) -> all artifacts written directly into ``build/test-outputs``
#                   (later writers overwrite earlier same-named files).
_REPO_ROOT = Path(__file__).resolve().parent.parent
_FLAT_OUTPUT = bool(os.environ.get("PY2MAX_TEST_OUTPUT_FLAT"))
TEST_OUTPUT_ROOT = _REPO_ROOT / "build" / (
    "test-outputs" if _FLAT_OUTPUT else "test-output"
)


@pytest.fixture(scope="session", autouse=True)
def _reset_test_output_root():
    """Wipe and recreate the test-output root once per session.

    Test artifacts land here (rather than a throwaway ``tmp_path``) so they
    survive a run for inspection. Clearing the tree at session start keeps runs
    reproducible and prevents the stale-artifact accumulation a persistent
    shared directory would otherwise cause.
    """
    if TEST_OUTPUT_ROOT.exists():
        shutil.rmtree(TEST_OUTPUT_ROOT)
    TEST_OUTPUT_ROOT.mkdir(parents=True)
    # In flat mode every test shares this root as its working directory, so the
    # ``outputs`` alias is created once for the whole session.
    outputs_link = TEST_OUTPUT_ROOT / "outputs"
    if _FLAT_OUTPUT:
        outputs_link.symlink_to(".")
    yield TEST_OUTPUT_ROOT
    # Drop the shared ``outputs`` alias so the flat tree holds only artifacts.
    if _FLAT_OUTPUT and outputs_link.is_symlink():
        outputs_link.unlink()


def _slugify_nodeid(nodeid: str) -> str:
    """Turn a pytest node id into a short, filesystem-safe directory name.

    ``tests/test_amxd.py::test_build_amxd_demo_tone`` becomes
    ``test_amxd__test_build_amxd_demo_tone`` -- the ``tests/`` prefix and ``.py``
    suffix are dropped and the remaining separators collapsed to underscores.
    """
    if nodeid.startswith("tests/"):
        nodeid = nodeid[len("tests/") :]
    nodeid = nodeid.replace(".py::", "__")
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", nodeid).strip("_")


@pytest.fixture(autouse=True)
def _isolate_cwd(request, monkeypatch, _reset_test_output_root):
    """Run each test in a working directory under the test-output root.

    Many tests write patches to a relative ``outputs/`` path. ``outputs`` is a
    symlink back to the working directory, so ``outputs/foo.maxpat`` writes land
    directly in ``<work_dir>/foo.maxpat`` with no extra nesting level.

    In the default (isolated) mode each test gets its own subdirectory so no two
    tests collide on a shared filename; the ``outputs`` alias is removed on
    teardown and a directory that captured no files is dropped, keeping the tree
    readable. In flat mode (``PY2MAX_TEST_OUTPUT_FLAT``) every test shares the
    root directory and artifacts accumulate there directly.

    Tests that read fixtures use paths anchored at ``__file__`` (e.g. a module
    ``DATA_DIR``), so they are unaffected by the working-directory change.
    """
    if _FLAT_OUTPUT:
        # Shared flat directory; the ``outputs`` alias is session-scoped and
        # artifacts persist, so there is nothing to set up or tear down here.
        monkeypatch.chdir(_reset_test_output_root)
        yield
        return

    work_dir = _reset_test_output_root / _slugify_nodeid(request.node.nodeid)
    work_dir.mkdir(parents=True, exist_ok=True)
    outputs_link = work_dir / "outputs"
    if not outputs_link.exists():
        outputs_link.symlink_to(".")
    monkeypatch.chdir(work_dir)
    yield
    # Drop the ``outputs`` alias and any directory that captured no artifacts.
    if outputs_link.is_symlink():
        outputs_link.unlink()
    if not any(p.is_file() for p in work_dir.rglob("*")):
        shutil.rmtree(work_dir, ignore_errors=True)
