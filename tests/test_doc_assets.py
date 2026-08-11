"""Tier 3 — the committed figures do not churn.

The demo writes its plots into ``docs/demos/datatypes/images/``, which is tracked
in git.  Rebuilding must therefore leave those files byte-identical, or every run
of the demo shows up as a repository change.

Two things have to hold for that, and both are easy to break by accident:

* the sample data must be generated from a fixed seed
* the figure must only be copied over the tracked file when the bytes differ,
  because matplotlib does not render byte-identical PNGs across runs
"""
from __future__ import annotations

import subprocess

import pytest

from .conftest import DATATYPES_DIR, REPO_ROOT

IMAGES_DIR = REPO_ROOT / "docs" / "demos" / "datatypes" / "images"


@pytest.fixture
def prepared(datatypes, tmp_path):
    """Vectors and golden data in a temporary root, ready for plotting."""
    datatypes.gen_samp_pack_vectors(tmp_path / "vectors")
    return tmp_path


class TestFiguresAreStable:
    def test_samp_pack_figure_is_unchanged_on_a_second_render(self, datatypes, prepared):
        images = prepared / "images"
        datatypes.plot_samp_pack(prepared / "vectors", prepared / "results", images)
        first = (images / "samp_pack_iq.png").read_bytes()

        datatypes.plot_samp_pack(prepared / "vectors", prepared / "results", images)
        assert (images / "samp_pack_iq.png").read_bytes() == first

    def test_tracked_file_is_not_touched_when_identical(self, datatypes, prepared):
        images = prepared / "images"
        datatypes.plot_samp_pack(prepared / "vectors", prepared / "results", images)
        before = (images / "samp_pack_iq.png").stat().st_mtime_ns

        datatypes.plot_samp_pack(prepared / "vectors", prepared / "results", images)
        assert (images / "samp_pack_iq.png").stat().st_mtime_ns == before

    def test_int_prod_figure_is_unchanged_on_a_second_render(self, datatypes, tmp_path):
        images = tmp_path / "images"
        datatypes.plot_int_prod(tmp_path / "vectors", tmp_path / "results", images)
        first = (images / "int_prod_overflow.png").read_bytes()

        datatypes.plot_int_prod(tmp_path / "vectors", tmp_path / "results", images)
        assert (images / "int_prod_overflow.png").read_bytes() == first


class TestCommittedFigures:
    def test_the_figures_the_docs_reference_exist(self):
        for name in ("int_prod_overflow.png", "samp_pack_iq.png"):
            assert (IMAGES_DIR / name).exists(), f"{name} is referenced by the docs"

    def test_docs_reference_only_figures_that_exist(self):
        import re
        for page in (REPO_ROOT / "docs" / "demos" / "datatypes").glob("*.md"):
            for src in re.findall(r'<img src="images/([^"]+)"', page.read_text(encoding="utf-8")):
                assert (IMAGES_DIR / src).exists(), f"{page.name} references missing {src}"

    def test_images_directory_is_clean_in_git(self):
        """The point of write-if-different: a rebuild must not dirty the repo."""
        proc = subprocess.run(
            ["git", "status", "--porcelain", "--", str(IMAGES_DIR)],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            pytest.skip("git not available")
        dirty = [ln for ln in proc.stdout.splitlines() if ln and not ln.startswith("??")]
        assert not dirty, f"committed figures were modified by a rebuild: {dirty}"


class TestBuildScriptIsRunnable:
    def test_list_steps_verbose_succeeds(self):
        """--list-steps-verbose is what the docs tell students to run first."""
        import sys
        proc = subprocess.run(
            [sys.executable, str(DATATYPES_DIR / "datatypes_build.py"), "--list-steps-verbose"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        assert "int_prod_gen" in proc.stdout
        assert "samp_pack_docs" in proc.stdout
