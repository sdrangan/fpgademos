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

import re
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


class TestDocsMatchTheCode:
    """The demo pages quote source and name steps; both can silently go stale."""

    #: Fragments quoted in steps.md / python.md that must still exist verbatim.
    QUOTED = [
        'consumes = ["int_prod_source"]',
        'produces = {"int_prod_vectors": Path("vectors/int_prod_in.csv")}',
        'dag.add(SourceStep(artifact="int_prod_source"',
        'outputs={"int_prod_sv": Path("vectors/int_prod_sv.csv")}',
        'plusargs={"vecdir": Path("vectors")}',
        "def wrap(value, width: int):",
        'golden.to_csv(vec_dir / "int_prod_golden.csv", index=False)',
        'diff = golden.compare(actual, result_names=("python", "systemverilog"))',
        "def saturate(value, width: int):",
        '"overflow": (prod != trunc).astype(np.int64),',
    ]

    def test_quoted_code_still_exists(self):
        source = (DATATYPES_DIR / "datatypes_build.py").read_text(encoding="utf-8")
        missing = [frag for frag in self.QUOTED if frag not in source]
        assert not missing, f"docs quote code that no longer exists: {missing}"

    def test_internal_links_resolve(self):
        import re
        pages = REPO_ROOT / "docs" / "demos" / "datatypes"
        broken = []
        for page in pages.glob("*.md"):
            text = page.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(\./([A-Za-z0-9_]+\.md)", text):
                if not (pages / target).exists():
                    broken.append(f"{page.name} -> {target}")
        assert not broken, f"broken links between demo pages: {broken}"

    def test_anchor_links_resolve(self):
        import re
        pages = REPO_ROOT / "docs" / "demos" / "datatypes"

        def anchors(path):
            out = set()
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("#"):
                    title = line.lstrip("#").strip().lower()
                    out.add(re.sub(r"[^a-z0-9\s-]", "", title).replace(" ", "-"))
            return out

        broken = []
        for page in pages.glob("*.md"):
            for target, anchor in re.findall(
                    r"\]\(\./([A-Za-z0-9_]+\.md)#([a-z0-9-]+)\)",
                    page.read_text(encoding="utf-8")):
                if (pages / target).exists() and anchor not in anchors(pages / target):
                    broken.append(f"{page.name} -> {target}#{anchor}")
        assert not broken, f"links to headings that do not exist: {broken}"

    def test_every_page_declares_front_matter(self):
        for page in (REPO_ROOT / "docs" / "demos" / "datatypes").glob("*.md"):
            head = page.read_text(encoding="utf-8").split("---")[1]
            assert "title:" in head and "nav_order:" in head, f"{page.name} front matter"

    def test_child_pages_have_distinct_nav_order(self):
        import re
        orders = {}
        for page in (REPO_ROOT / "docs" / "demos" / "datatypes").glob("*.md"):
            if page.name == "index.md":
                continue          # the parent; its order is relative to Demos
            order = int(re.search(r"nav_order:\s*(\d+)", page.read_text(encoding="utf-8"))[1])
            orders.setdefault(order, []).append(page.name)
        clashes = {k: v for k, v in orders.items() if len(v) > 1}
        assert not clashes, f"pages share a nav_order: {clashes}"


class TestMermaidDiagrams:
    """just-the-docs only loads Mermaid when a version is pinned in _config.yml.

    Without it the ```mermaid fences render as plain code blocks -- the diagrams
    do not error, they just quietly turn back into text, which is the kind of
    regression nobody notices until a student mentions it.
    """

    def _blocks(self):
        import re
        pages = REPO_ROOT / "docs" / "demos" / "datatypes"
        for page in sorted(pages.glob("*.md")):
            text = page.read_text(encoding="utf-8")
            for src in re.findall(r"```mermaid\r?\n(.*?)```", text, re.DOTALL):
                yield page.name, src

    def test_config_pins_a_mermaid_version(self):
        config = (REPO_ROOT / "_config.yml").read_text(encoding="utf-8")
        assert "mermaid:" in config, "_config.yml does not enable Mermaid"
        assert re.search(r"mermaid:\s*\n\s*version:\s*\"[\d.]+\"", config), \
            "Mermaid is enabled but no version is pinned; just-the-docs will not load it"

    def test_pages_actually_use_mermaid(self):
        assert list(self._blocks()), "no Mermaid blocks found — did a page lose its diagram?"

    def test_every_block_declares_a_diagram_type(self):
        known = ("flowchart", "graph", "sequenceDiagram", "classDiagram",
                 "stateDiagram", "erDiagram", "gantt", "pie", "block-beta")
        bad = [(name, src.strip().splitlines()[0])
               for name, src in self._blocks()
               if not src.strip().startswith(known)]
        assert not bad, f"Mermaid blocks with no recognised diagram type: {bad}"

    def test_no_unclosed_fences(self):
        for page in (REPO_ROOT / "docs" / "demos" / "datatypes").glob("*.md"):
            text = page.read_text(encoding="utf-8")
            assert text.count("```mermaid") == len(
                re.findall(r"```mermaid\r?\n.*?```", text, re.DOTALL)), \
                f"{page.name} has an unclosed ```mermaid fence"


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
