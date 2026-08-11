"""Tier 0 — the build graph is well formed.

Runs in milliseconds and needs no tools.  Artifact-name typos in ``consumes`` /
``produces`` are the classic BuildDag mistake, and without a check like this they
surface only at run time, on a student's machine, as a confusing error.
"""
from __future__ import annotations

import pytest

DOCUMENTED_THROUGH_TARGETS = [
    "int_prod_gen", "int_prod_sim", "int_prod_check", "int_prod_docs",
    "samp_pack_gen", "samp_pack_sim", "samp_pack_check", "samp_pack_docs",
]


@pytest.fixture
def dag(datatypes):
    return datatypes.build_datatypes_dag()


class TestGraphShape:
    def test_documented_step_names_exist(self, dag):
        """Every --through target named in the docs must be a real step."""
        names = set(dag.step_names())
        missing = [t for t in DOCUMENTED_THROUGH_TARGETS if t not in names]
        assert not missing, f"documented but absent: {missing}"

    def test_every_consumed_artifact_has_a_producer(self, dag):
        produced = set()
        for step in dag.steps():
            produced.update(step.produces)
        dangling = {step.name: [c for c in step.consumes if c not in produced]
                    for step in dag.steps()}
        dangling = {k: v for k, v in dangling.items() if v}
        assert not dangling, f"consumed but never produced: {dangling}"

    def test_no_artifact_has_two_producers(self, dag):
        seen: dict[str, str] = {}
        clashes = []
        for step in dag.steps():
            for artifact in step.produces:
                if artifact in seen:
                    clashes.append((artifact, seen[artifact], step.name))
                seen[artifact] = step.name
        assert not clashes, f"artifacts produced twice: {clashes}"

    def test_topological_order_puts_producers_first(self, dag):
        available: set[str] = set()
        for step in dag.steps():
            unmet = [c for c in step.consumes if c not in available]
            assert not unmet, f"{step.name} consumes {unmet} before they are produced"
            available.update(step.produces)

    def test_every_step_describes_itself(self, dag):
        """--list-steps-verbose is the demo's self-documentation; blanks defeat it."""
        undescribed = [s.name for s in dag.steps() if not s.description]
        assert not undescribed

    def test_the_two_parts_are_independent(self, dag):
        """samp_pack must not depend on int_prod, or --through cannot isolate them."""
        owners = {a: s.name for s in dag.steps() for a in s.produces}
        for step in dag.steps():
            if step.name.startswith("samp_pack"):
                upstream = [owners[c] for c in step.consumes]
                assert not [u for u in upstream if u.startswith("int_prod")]


class TestArtifactPaths:
    def test_sim_steps_declare_the_files_the_testbench_writes(self, dag):
        """Not just the scratch directory: a run that died still leaves sim/ behind."""
        for name in ("int_prod_sim", "samp_pack_sim"):
            step = next(s for s in dag.steps() if s.name == name)
            assert any("_sv.txt" in str(p) for p in step.produces.values()), \
                f"{name} does not declare its testbench output"

    def test_doc_steps_write_into_the_tracked_images_directory(self, dag, datatypes):
        for name in ("int_prod_docs", "samp_pack_docs"):
            step = next(s for s in dag.steps() if s.name == name)
            paths = [str(p).replace("\\", "/") for p in step.produces.values()]
            assert all("docs/demos/datatypes/images" in p for p in paths)
