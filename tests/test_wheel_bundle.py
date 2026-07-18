"""R2: guarantee the offline maxref bundle ships inside the built wheel.

The whole introspection / connection-validation stack depends on
``py2max/maxref/data/bundle.json.gz``. If it ever drops out of the wheel,
``maxref`` silently degrades to an empty refdict and validation becomes a no-op
-- no error, just wrong behaviour. The pre-existing shipping check resolved the
path relative to ``parser.__file__``, which passes trivially in the source tree
and proves nothing about a *built* artifact. This test builds the wheel and
inspects the archive directly.
"""

import gzip
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

BUNDLE_ARCNAME = "py2max/maxref/data/bundle.json.gz"
REPO_ROOT = Path(__file__).resolve().parent.parent


def _repo_has_build_backend() -> bool:
    return (REPO_ROOT / "pyproject.toml").is_file()


@pytest.mark.skipif(shutil.which("uv") is None, reason="requires the uv build tool")
@pytest.mark.skipif(not _repo_has_build_backend(), reason="not run from a source checkout")
def test_built_wheel_contains_maxref_bundle(tmp_path):
    """Build the wheel and assert the compressed bundle is really inside it."""
    result = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"wheel build failed:\n{result.stderr}"

    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, got {wheels}"

    with zipfile.ZipFile(wheels[0]) as zf:
        names = zf.namelist()
        assert BUNDLE_ARCNAME in names, (
            f"{BUNDLE_ARCNAME} missing from wheel; introspection/validation "
            f"would silently no-op. Wheel entries: {names}"
        )

        raw = zf.read(BUNDLE_ARCNAME)

    # It must be a non-trivial, valid gzip-JSON payload, not an empty placeholder.
    assert len(raw) > 100_000, f"bundle suspiciously small ({len(raw)} bytes)"
    data = json.loads(gzip.decompress(raw))
    objects = data.get("objects", {})
    assert isinstance(objects, dict) and len(objects) > 1000, (
        f"bundle should hold the full object catalog, got {len(objects)} entries"
    )


def test_installed_bundle_is_readable():
    """Cheap always-on check: the bundle is loadable from the installed package.

    Complements the wheel test above -- this one runs even without the build
    tool and proves the currently-imported py2max can actually read the bundle.
    """
    try:
        from importlib.resources import files
    except ImportError:  # pragma: no cover - py<3.9 fallback, unused here
        pytest.skip("importlib.resources.files unavailable")

    resource = files("py2max.maxref").joinpath("data/bundle.json.gz")
    assert resource.is_file(), "bundle.json.gz not present in installed package"
    data = json.loads(gzip.decompress(resource.read_bytes()))
    assert isinstance(data.get("objects"), dict) and len(data["objects"]) > 1000
