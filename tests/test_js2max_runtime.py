"""The js2max JavaScript runtime ships with the package and can be installed.

Without this, js2max exists only in the source repository and nobody who
installs py2max from PyPI can use it at all.

The load-bearing guarantee is not convenience but **version agreement**:
``js2max/src/objects.ts`` -- box classes, port counts and outlet types for 1098
object classes -- is generated from this package's maxref bundle. A runtime
built against one version of py2max and used with another declares wrong port
counts for whatever changed, and a box declaring a port it does not have loses
the cord attached to it when Max opens the file. Shipping both in one artifact
is what makes that impossible, so these tests check they agree.
"""

import json
import re
import subprocess
import zipfile
from pathlib import Path

import pytest

from py2max import Patcher, js2max_runtime

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_BUNDLES = REPO_ROOT / "js2max" / "max"


class TestTheRuntimeIsPresent:
    def test_both_builds_are_shipped(self):
        for flavor in ("v8", "commonjs"):
            bundle = js2max_runtime.path(flavor)
            assert bundle.exists()
            assert bundle.stat().st_size > 10_000

    def test_the_v8_build_is_the_default(self):
        assert js2max_runtime.path().name == "js2max.v8.js"
        assert js2max_runtime.path().name == js2max_runtime.V8_BUNDLE

    def test_an_unknown_build_names_the_ones_that_exist(self):
        with pytest.raises(ValueError, match="commonjs, v8"):
            js2max_runtime.path("esm")

    def test_the_shipped_copy_matches_the_repository_copy(self):
        # The runtime is built into `js2max/max/` for Max, and mirrored into the
        # package so it ships. Byte-identity is what makes that duplication
        # safe: a shipped runtime that lagged the repository one would declare
        # stale port counts, silently.
        if not REPO_BUNDLES.exists():
            pytest.skip("js2max sources not present (installed package)")
        for flavor, filename in js2max_runtime.BUNDLE_FILENAMES.items():
            assert (
                js2max_runtime.path(flavor).read_bytes()
                == (REPO_BUNDLES / filename).read_bytes()
            ), f"{filename} differs between js2max/max/ and the package"


class TestTheRuntimeAgreesWithThisPyMax:
    """The version-skew guarantee, which is the reason for shipping together."""

    def test_port_counts_in_the_bundle_match_py2max(self):
        from py2max import maxref

        source = js2max_runtime.path().read_text()

        # `PORTS` is emitted as `name: [numinlets, numoutlets, ...]`, with the
        # key quoted only when it is not a valid JS identifier -- so `metro:`
        # but `"cycle~":`. Sampling classes a real patch is built from is
        # enough: the point is that the two came from one generation, not to
        # re-verify the generator.
        for name in ("cycle~", "gain~", "ezdac~", "metro", "mtof"):
            defaults = maxref.MAXCLASS_DEFAULTS.get(name) or {}
            if "numinlets" not in defaults or "numoutlets" not in defaults:
                continue
            entry = re.compile(
                rf'"?{re.escape(name)}"?:\s*\['
                rf'{defaults["numinlets"]},\s*{defaults["numoutlets"]}\b'
            )
            assert entry.search(source), f"{name} disagrees with py2max's maxref data"

    def test_the_bundle_declares_the_same_max_version(self):
        from py2max.core.patcher import (
            MAX_VER_MAJOR,
            MAX_VER_MINOR,
            MAX_VER_REVISION,
        )

        source = js2max_runtime.path().read_text()
        for label, value in (
            ("major", MAX_VER_MAJOR),
            ("minor", MAX_VER_MINOR),
            ("revision", MAX_VER_REVISION),
        ):
            assert re.search(rf"{label}:\s*{value}\b", source), (
                f"bundle does not declare {label} {value}"
            )


class TestInstall:
    def test_installing_into_a_directory(self, tmp_path):
        installed = js2max_runtime.install(tmp_path)

        assert installed == tmp_path / "js2max.v8.js"
        assert installed.read_bytes() == js2max_runtime.path().read_bytes()

    def test_installing_to_an_explicit_filename(self, tmp_path):
        installed = js2max_runtime.install(tmp_path / "sub" / "bridge.js")

        assert installed.name == "bridge.js"
        assert installed.exists()

    def test_installing_twice_is_a_no_op(self, tmp_path):
        first = js2max_runtime.install(tmp_path)
        stamp = first.stat().st_mtime_ns
        again = js2max_runtime.install(tmp_path)

        # `save()` installs on every call; rewriting the file each time would
        # churn timestamps for no reason.
        assert again == first
        assert again.stat().st_mtime_ns == stamp

    def test_a_stale_copy_is_replaced(self, tmp_path):
        (tmp_path / "js2max.v8.js").write_text("// an older build")

        installed = js2max_runtime.install(tmp_path)
        assert installed.read_bytes() == js2max_runtime.path().read_bytes()


class TestAddV8Bridge:
    def test_the_box_is_what_max_expects(self, tmp_path):
        p = Patcher(str(tmp_path / "b.maxpat"))
        box = p.add_v8_bridge()

        assert box.maxclass == "newobj"
        assert box.text == "v8 js2max.v8.js"
        # From the maxref table, like any other object box.
        assert box.numinlets == 1
        assert box.numoutlets == 1

    def test_saving_writes_the_runtime_beside_the_patch(self, tmp_path):
        path = tmp_path / "builder.maxpat"
        p = Patcher(str(path))
        p.add_v8_bridge()
        p.save()

        assert sorted(q.name for q in tmp_path.iterdir()) == [
            "builder.maxpat",
            "js2max.v8.js",
        ]

    def test_a_patch_without_the_bridge_writes_only_itself(self, tmp_path):
        p = Patcher(str(tmp_path / "plain.maxpat"))
        p.add_textbox("cycle~ 440")
        p.save()

        assert [q.name for q in tmp_path.iterdir()] == ["plain.maxpat"]

    def test_save_as_installs_next_to_the_written_file(self, tmp_path):
        p = Patcher(str(tmp_path / "unused.maxpat"))
        p.add_v8_bridge()
        elsewhere = tmp_path / "out"
        p.save_as(elsewhere / "b.maxpat")

        assert (elsewhere / "js2max.v8.js").exists()
        assert not (tmp_path / "js2max.v8.js").exists()

    def test_a_custom_bundle_name_is_used_verbatim(self, tmp_path):
        p = Patcher(str(tmp_path / "b.maxpat"))
        box = p.add_v8_bridge(bundle="my-bridge.js")

        assert box.text == "v8 my-bridge.js"

    def test_a_custom_bundle_name_installs_nothing(self, tmp_path):
        # A caller naming their own file has placed it themselves. Copying
        # `js2max.v8.js` next to a patch that refers to something else would be
        # both useless and surprising -- and it is also the escape hatch for the
        # single-file edition, which cannot carry the runtime.
        p = Patcher(str(tmp_path / "own.maxpat"))
        p.add_v8_bridge(bundle="my-bridge.js")
        p.save()

        assert [q.name for q in tmp_path.iterdir()] == ["own.maxpat"]

    def test_the_bridge_box_wires_up_like_any_other(self, tmp_path):
        p = Patcher(str(tmp_path / "b.maxpat"))
        bridge = p.add_v8_bridge()
        printer = p.add_textbox("print js2max")
        p.add_line(bridge, printer)

        d = p.to_dict()["patcher"]
        assert len(d["lines"]) == 1
        assert d["lines"][0]["patchline"]["source"][0] == bridge.id


def _repo_has_build_backend() -> bool:
    return (REPO_ROOT / "pyproject.toml").exists()


@pytest.mark.skipif(not _repo_has_build_backend(), reason="not a source checkout")
class TestTheRuntimeShipsInTheWheel:
    """A source-tree path passes trivially and proves nothing about a wheel.

    Same reasoning as ``test_wheel_bundle.py``, which exists because the maxref
    bundle dropping out of the wheel degrades silently.
    """

    @pytest.fixture(scope="class")
    def wheel(self, tmp_path_factory):
        out = tmp_path_factory.mktemp("wheel")
        result = subprocess.run(
            ["uv", "build", "--wheel", "--out-dir", str(out)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip(f"wheel build unavailable: {result.stderr[-300:]}")
        wheels = list(out.glob("*.whl"))
        if not wheels:
            pytest.skip("no wheel produced")
        return wheels[0]

    def test_both_bundles_are_in_the_archive(self, wheel):
        with zipfile.ZipFile(wheel) as archive:
            names = set(archive.namelist())
            for filename in js2max_runtime.BUNDLE_FILENAMES.values():
                arcname = f"py2max/data/js2max/{filename}"
                assert arcname in names, f"{arcname} missing from the wheel"
                assert archive.getinfo(arcname).file_size > 10_000

    def test_the_archived_bundle_is_the_one_in_the_tree(self, wheel):
        with zipfile.ZipFile(wheel) as archive:
            shipped = archive.read(f"py2max/data/js2max/{js2max_runtime.V8_BUNDLE}")
        assert shipped == js2max_runtime.path().read_bytes()


class TestTheGeneratedPatchPattern:
    def test_a_dict_driven_builder_patch_round_trips(self, tmp_path):
        # The pattern the runtime exists for: py2max writes a description as
        # JSON, a [dict] loads it, and the bridge builds it inside Max.
        described = Patcher(str(tmp_path / "described.maxpat"))
        described.add_textbox("cycle~ 440")
        (tmp_path / "described.json").write_text(described.to_json())

        p = Patcher(str(tmp_path / "builder.maxpat"))
        bridge = p.add_v8_bridge()
        loader = p.add_message("import described.json")
        holder = p.add_textbox("dict js2max_patch")
        builder = p.add_message("builddict js2max_patch")
        p.add_line(loader, holder)
        p.add_line(builder, bridge)
        p.save()

        assert (tmp_path / "js2max.v8.js").exists()
        emitted = json.loads((tmp_path / "builder.maxpat").read_text())
        texts = [b["box"].get("text") for b in emitted["patcher"]["boxes"]]
        assert "v8 js2max.v8.js" in texts
        assert "builddict js2max_patch" in texts
