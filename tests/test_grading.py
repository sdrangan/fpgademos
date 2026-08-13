"""Tier 0 — the grading steps behave the way a lab depends on them behaving.

The three properties worth a test are the three that are *not* obvious from
reading ``GradedStep``, because each one is a consequence of how
``BuildDag.run`` is written rather than of anything in this repository:

* a zero does not halt the build, but a crash does;
* the eval record is written on both paths;
* a skipped step still has a readable score.
"""
from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
import pytest
from waveflow.build.build import BuildConfig, BuildDag

from hwdesign.grading import (
    Checks, GradeReportStep, GradeResult, GradedStep, StudentSourceStep, format_eval,
    print_grade_summary,
)


# ---------------------------------------------------------------------------
# Fixtures: a two-step lab, with the first step's score under test control
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class _GenStep(GradedStep):
    """Writes a file and grades it; ``award`` decides what it scores."""

    description = "Generate a value and grade it."
    points = 10.0
    outputs = {"gen_out": Path("out/gen.txt")}
    consumes = []

    award: float = 10.0
    explode: bool = False

    def evaluate(self, config: BuildConfig, **_) -> GradeResult:
        if self.explode:
            raise RuntimeError("the toolchain fell over")
        path = config.root_dir / "out/gen.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("42", encoding="utf-8")

        checks = Checks()
        checks.that(self.award >= 5, 5, "PRNG values are in range", "3 values exceeded 255")
        checks.that(self.award >= 10, 5, "Values are uniform", "chi-square p = 0.001")
        return checks.result(gen_out=path)


@dataclass(kw_only=True)
class _CheckStep(GradedStep):
    """Consumes the first step's output — the canary for 'did the build continue?'."""

    description = "Read what the first step wrote and grade it."
    points = 6.0
    outputs = {"check_out": Path("out/check.txt")}
    consumes = ["gen_out"]

    def evaluate(self, config: BuildConfig, gen_out: Path, **_) -> GradeResult:
        path = config.root_dir / "out/check.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(Path(gen_out).read_text(encoding="utf-8"), encoding="utf-8")

        checks = Checks()
        checks.fraction(1.0, 6, "SystemVerilog matches the Python model")
        return checks.result(check_out=path)


def _lab(tmp_path: Path, *, award: float = 10.0, explode: bool = False):
    gen = _GenStep(name="prng_py", title="Python PRNG model", award=award,
                   explode=explode, verbose=False)
    check = _CheckStep(name="prng_sim", title="SystemVerilog PRNG", verbose=False)
    dag = BuildDag()
    dag.add(gen)
    dag.add(check)
    return dag, [gen, check], BuildConfig(root_dir=tmp_path)


# ---------------------------------------------------------------------------
# The record
# ---------------------------------------------------------------------------

def test_eval_record_has_score_and_feedback(tmp_path):
    dag, (gen, _), config = _lab(tmp_path, award=5)
    dag.run(config, through="prng_py")

    record = json.loads((tmp_path / "eval/prng_py.json").read_text(encoding="utf-8"))
    assert (record["score"], record["max_score"]) == (5.0, 10.0)
    assert record["title"] == "Python PRNG model"
    assert record["error"] is None
    assert record["feedback"] == [
        "✓ (5/5) PRNG values are in range",
        "✗ (0/5) Values are uniform — chi-square p = 0.001",
    ]


def test_eval_artifact_is_produced_and_named_per_step(tmp_path):
    dag, (gen, check), config = _lab(tmp_path)
    assert gen.eval_artifact == "prng_py_eval"
    assert set(gen.produces) == {"prng_py_eval", "gen_out"}
    assert dag.artifact_paths(config)["prng_sim_eval"] == tmp_path / "eval/prng_sim.json"


def test_format_eval_is_the_line_a_student_sees(tmp_path):
    dag, _, config = _lab(tmp_path, award=5)
    dag.run(config, through="prng_py")
    record = json.loads((tmp_path / "eval/prng_py.json").read_text(encoding="utf-8"))
    assert format_eval(record).splitlines()[0] == "Python PRNG model: 5/10"


# ---------------------------------------------------------------------------
# Fact 1: a zero continues, a crash halts — and both leave a record
# ---------------------------------------------------------------------------

def test_a_bad_score_does_not_halt_the_build(tmp_path):
    """The whole point: partial credit must not cost the student the later stages."""
    dag, _, config = _lab(tmp_path, award=0)
    results = dag.run(config)

    assert results["prng_py"].success and results["prng_sim"].success
    assert json.loads((tmp_path / "eval/prng_py.json").read_text())["score"] == 0.0
    assert json.loads((tmp_path / "eval/prng_sim.json").read_text())["score"] == 6.0


def test_a_crash_halts_the_build_but_still_records_a_zero(tmp_path):
    dag, _, config = _lab(tmp_path, explode=True)
    results = dag.run(config)

    assert not results["prng_py"].success
    assert "prng_sim" not in results          # the DAG stopped, as it must
    record = json.loads((tmp_path / "eval/prng_py.json").read_text(encoding="utf-8"))
    assert (record["score"], record["max_score"]) == (0.0, 10.0)
    assert "the toolchain fell over" in record["error"]


def test_attempt_scores_a_student_exception_instead_of_raising():
    checks = Checks()
    with checks.attempt(4, "prng_next() returns a value"):
        raise IndexError("list index out of range")
    result = checks.result()

    assert (result.score, result.max_score) == (0.0, 4.0)
    assert "raised IndexError" in result.feedback[0]


# ---------------------------------------------------------------------------
# Fact 2: a skipped step still has a score
# ---------------------------------------------------------------------------

def test_score_survives_a_skipped_rerun(tmp_path, capsys):
    dag, steps, config = _lab(tmp_path, award=5)
    dag.run(config, through="prng_py")

    second = dag.run(config, through="prng_py")
    assert second["prng_py"].skipped

    capsys.readouterr()
    print_grade_summary(tmp_path, steps)
    out = capsys.readouterr().out
    assert "Python PRNG model: 5/10" in out
    assert "SystemVerilog PRNG: —/6  (not yet run)" in out
    assert "TOTAL 5/16" in out


# ---------------------------------------------------------------------------
# "Not started" is not the same as "wrong"
# ---------------------------------------------------------------------------

def _seeded_lab(tmp_path: Path):
    """A lab whose one student file is seeded from partial/, as a real one is."""
    (tmp_path / "partial").mkdir()
    (tmp_path / "partial" / "work.py").write_text("# TODO\n", encoding="utf-8")

    src = StudentSourceStep(artifact="gen_out", path=Path("work.py"))

    @dataclass(kw_only=True)
    class _Graded(GradedStep):
        description = "grades work.py"
        points = 10.0
        consumes = ["gen_out"]

        def evaluate(self, config, **_):
            checks = Checks()
            # Vacuously satisfied by the untouched template — which is exactly
            # the partial credit that must not be paid before work has started.
            checks.that(True, 7, "the file exists")
            checks.that(False, 3, "the work is done", "nothing implemented")
            return checks.result()

    step = _Graded(name="stage", title="The stage", verbose=False, starts_from=[src])
    dag = BuildDag()
    dag.add(src)
    dag.add(step)
    return dag, src, step, BuildConfig(root_dir=tmp_path)


def test_first_run_seeds_the_file_and_reports_not_started(tmp_path):
    """A student's opening move must not read as a failing grade."""
    dag, _, _, config = _seeded_lab(tmp_path)
    dag.run(config)

    assert (tmp_path / "work.py").read_text(encoding="utf-8") == "# TODO\n"
    record = json.loads((tmp_path / "eval/stage.json").read_text(encoding="utf-8"))
    assert record["score"] == 0.0          # not the 7 the vacuous check would pay
    assert "not started" in record["feedback"][0]
    assert "work.py" in record["feedback"][0]


def test_an_edited_file_is_graded_normally(tmp_path):
    dag, _, _, config = _seeded_lab(tmp_path)
    dag.run(config)
    (tmp_path / "work.py").write_text("# TODO\nimplemented = True\n", encoding="utf-8")

    dag.run(config, force=True)
    record = json.loads((tmp_path / "eval/stage.json").read_text(encoding="utf-8"))
    assert record["score"] == 7.0
    assert "not started" not in " ".join(record["feedback"])


def test_force_never_overwrites_student_work(tmp_path):
    """--force re-runs every step; it must not restore the template over an edit."""
    dag, _, _, config = _seeded_lab(tmp_path)
    dag.run(config)
    (tmp_path / "work.py").write_text("my work\n", encoding="utf-8")

    dag.run(config, force=True)
    assert (tmp_path / "work.py").read_text(encoding="utf-8") == "my work\n"


def test_a_missing_template_grades_normally_rather_than_excusing(tmp_path):
    """With nothing to compare against, grade — do not assume work is unstarted."""
    dag, src, _, config = _seeded_lab(tmp_path)
    dag.run(config)
    (tmp_path / "partial" / "work.py").unlink()

    assert src.is_untouched(config) is False
    dag.run(config, force=True)
    assert json.loads((tmp_path / "eval/stage.json").read_text())["score"] == 7.0


def test_not_started_still_produces_downstream_artifacts(tmp_path):
    """evaluate() must still run, or the stages after this one have nothing to read."""
    (tmp_path / "partial").mkdir()
    (tmp_path / "partial" / "work.py").write_text("# TODO\n", encoding="utf-8")
    src = StudentSourceStep(artifact="gen_out", path=Path("work.py"))

    @dataclass(kw_only=True)
    class _Producing(GradedStep):
        description = "produces a file and grades it"
        points = 5.0
        outputs = {"data": Path("out/data.txt")}
        consumes = ["gen_out"]

        def evaluate(self, config, **_):
            path = Path(config.root_dir) / "out/data.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("generated anyway", encoding="utf-8")
            checks = Checks()
            checks.that(True, 5, "vacuous")
            return checks.result(data=path)

    dag = BuildDag()
    dag.add(src)
    dag.add(_Producing(name="stage", verbose=False, starts_from=[src]))
    results = dag.run(BuildConfig(root_dir=tmp_path))

    assert results["stage"].success
    assert (tmp_path / "out/data.txt").exists()
    assert json.loads((tmp_path / "eval/stage.json").read_text())["score"] == 0.0


# ---------------------------------------------------------------------------
# Authoring mistakes are caught, not silently mis-scored
# ---------------------------------------------------------------------------

def test_checks_totalling_something_other_than_points_is_an_error(tmp_path):
    @dataclass(kw_only=True)
    class _Mismatched(GradedStep):
        description = "declares 10, checks total 7"
        points = 10.0
        consumes = []

        def evaluate(self, config, **_):
            checks = Checks()
            checks.that(True, 7, "worth seven")
            return checks.result()

    dag = BuildDag()
    dag.add(_Mismatched(name="wrong", verbose=False))
    results = dag.run(BuildConfig(root_dir=tmp_path))
    assert "declares points=10 but its checks total 7" in results["wrong"].message


def test_outputs_not_returned_is_an_error(tmp_path):
    @dataclass(kw_only=True)
    class _Forgetful(GradedStep):
        description = "declares an output it never returns"
        points = 1.0
        outputs = {"never": Path("out/never.txt")}
        consumes = []

        def evaluate(self, config, **_):
            checks = Checks()
            checks.that(True, 1, "graded fine, but wrote nothing")
            return checks.result()

    dag = BuildDag()
    dag.add(_Forgetful(name="forgetful", verbose=False))
    results = dag.run(BuildConfig(root_dir=tmp_path))
    assert "did not return them" in results["forgetful"].message


@pytest.mark.parametrize("frac,expected", [(-1.0, 0.0), (0.5, 2.0), (2.0, 4.0)])
def test_fraction_is_clamped(frac, expected):
    checks = Checks()
    checks.fraction(frac, 4, "partial credit")
    assert checks.result().score == expected


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

def test_report_writes_the_shape_gradescope_copies(tmp_path, capsys):
    dag, steps, config = _lab(tmp_path, award=5)
    (tmp_path / "prng.sv").write_text("// student work", encoding="utf-8")
    report = GradeReportStep(name="submit", graded=steps, bundle=[Path("prng.sv")])
    dag.add(report)

    dag.run(config)
    capsys.readouterr()

    results = json.loads((tmp_path / "submission/submitted_results.json").read_text(encoding="utf-8"))
    assert results["score"] == 11.0
    assert [t["name"] for t in results["tests"]] == ["Python PRNG model", "SystemVerilog PRNG"]
    assert [(t["score"], t["max_score"]) for t in results["tests"]] == [(5.0, 10.0), (6.0, 6.0)]
    # autograde.py copies this file to /autograder/results/results.json untouched,
    # so every key Gradescope needs has to already be here.
    assert set(results["tests"][0]) == {"name", "score", "max_score", "output"}
    assert "chi-square p = 0.001" in results["tests"][0]["output"]


def test_report_zip_holds_the_results_and_the_required_sources(tmp_path):
    dag, steps, config = _lab(tmp_path)
    (tmp_path / "prng.sv").write_text("// student work", encoding="utf-8")
    dag.add(GradeReportStep(name="submit", graded=steps, bundle=[Path("prng.sv")]))
    dag.run(config)

    with zipfile.ZipFile(tmp_path / "submission/submission.zip") as zf:
        assert sorted(zf.namelist()) == ["prng.sv", "submitted_results.json"]


def test_report_refuses_to_bundle_a_missing_required_file(tmp_path):
    dag, steps, config = _lab(tmp_path)
    dag.add(GradeReportStep(name="submit", graded=steps, bundle=[Path("prng.sv")]))
    results = dag.run(config)

    assert not results["submit"].success
    assert "required file(s) not found" in results["submit"].message
    assert not (tmp_path / "submission/submission.zip").exists()


def test_report_consumes_every_eval_so_it_cannot_bundle_a_stale_score(tmp_path):
    dag, steps, config = _lab(tmp_path)
    report = GradeReportStep(name="submit", graded=steps, bundle=[])
    dag.add(report)
    assert report.consumes == ["prng_py_eval", "prng_sim_eval"]
