"""Shared pytest fixtures for the py2max test suite."""

import logging
import os
import re
import shutil
from pathlib import Path

import pytest

from py2max import Patcher
from py2max.log import LOGGER_NAME

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
TEST_OUTPUT_ROOT = (
    _REPO_ROOT / "build" / ("test-outputs" if _FLAT_OUTPUT else "test-output")
)


@pytest.fixture(autouse=True)
def _isolate_py2max_logger():
    """Restore the ``py2max`` logger after each test.

    ``setup_logging()`` mutates a process-global logger, so any test that calls it
    -- directly or via ``cli.main()`` -- would otherwise leak handlers and level
    into every test that runs afterwards. That once cost the suite a false
    failure: a CLI test's logging config made ``caplog`` blind to py2max records
    in a later lint test, which passed alone and failed in the full run.
    """
    logger = logging.getLogger(LOGGER_NAME)
    saved = (list(logger.handlers), logger.level, logger.propagate)
    try:
        yield
    finally:
        logger.handlers[:] = saved[0]
        logger.setLevel(saved[1])
        logger.propagate = saved[2]


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


# -- signal_order A/B -------------------------------------------------------
#
# Every tests/test_layout* test runs twice, as [signal_on] and [signal_off], and
# every top-level Patcher it creates is saved into its per-test directory, so
# the two layouts sit side by side for inspection in Max. At session end,
# ``signal_order_ab.md`` in the output root lists the pairs that differ.
# test_layout_grid_order asserts signal-order behaviour itself, so it runs once.
# Flat mode runs once too: both variants would write the same file names.

_AB_EXCLUDED = {"test_layout_grid_order"}
_AB_IDS = {True: "signal_on", False: "signal_off"}


def pytest_generate_tests(metafunc):
    module = metafunc.module.__name__.rpartition(".")[2]
    if _FLAT_OUTPUT or not module.startswith("test_layout") or module in _AB_EXCLUDED:
        return
    metafunc.parametrize(
        "_ab_signal_order",
        list(_AB_IDS),
        ids=list(_AB_IDS.values()),
        indirect=True,
    )


@pytest.fixture(autouse=True)
def _ab_signal_order(request, monkeypatch, _isolate_cwd):
    """Default ``Patcher(signal_order=...)`` to the variant; save patches at teardown.

    Autouse so it is in every test's fixture closure; a test that
    ``pytest_generate_tests`` did not parametrize has no ``param`` and is untouched.
    """
    if not hasattr(request, "param"):
        yield None
        return
    created = []
    init = Patcher.__init__

    def patched_init(self, *args, **kwargs):
        kwargs.setdefault("signal_order", request.param)
        init(self, *args, **kwargs)
        created.append(self)

    monkeypatch.setattr(Patcher, "__init__", patched_init)
    yield request.param

    names: set = set()
    for i, p in enumerate(c for c in created if c._parent is None):
        name = Path(str(p._path)).name if p._path else f"patcher-{i}.maxpat"
        if name in names:
            name = f"{i}-{name}"
        names.add(name)
        try:
            p.save_as(Path.cwd() / name)
        except Exception:  # a test may leave a patcher deliberately unsavable
            pass
            pass


def pytest_sessionfinish(session, exitstatus):
    if _FLAT_OUTPUT or not TEST_OUTPUT_ROOT.exists():
        return
    differ, same = [], 0
    for on in sorted(TEST_OUTPUT_ROOT.glob("*signal_on*")):
        off = on.with_name(on.name.replace("signal_on", "signal_off"))
        files = sorted(
            {f.relative_to(on) for f in on.rglob("*") if f.is_file()}
            | (
                {f.relative_to(off) for f in off.rglob("*") if f.is_file()}
                if off.exists()
                else set()
            )
        )
        changed = [
            f
            for f in files
            if not (on / f).exists()
            or not (off / f).exists()
            or (on / f).read_bytes() != (off / f).read_bytes()
        ]
        if changed:
            differ.append((on.name.replace("signal_on", "*"), changed))
        else:
            same += 1
    if not differ and not same:
        return
    lines = [
        "# signal_order A/B",
        "",
        f"{len(differ)} test(s) differ between signal_order=True and False; "
        f"{same} produce identical patches.",
        "",
        "signal_order only affects grid-family layouts. A difference in another "
        "layout (e.g. kamada-kawai) means that layout is not deterministic.",
        "",
    ]
    for base, changed in differ:
        lines.append(f"- `{base}`: " + ", ".join(f"`{f}`" for f in changed))
    (TEST_OUTPUT_ROOT / "signal_order_ab.md").write_text("\n".join(lines) + "\n")
