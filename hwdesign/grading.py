"""grading — build steps that carry a score.

A lab is a :class:`~waveflow.build.build.BuildDag` whose nodes are
:class:`GradedStep`\\ s.  Each one does real work *and* grades it, writing a
small JSON record next to its other outputs.  A terminal :class:`GradeReportStep`
collects those records into the ``submitted_results.json`` that
`gradescope/autograde.py <../gradescope/autograde.py>`_ copies verbatim, plus the
zip the student uploads.

The student's loop is the DAG's::

    python prng_build.py --through prng_py     # score 5/10, and why
    python prng_build.py --through prng_sim    # ... and the next stage
    python prng_build.py                       # everything, then the zip

Why this lives in hwdesign and not waveflow: what a score *is* — partial credit,
Gradescope's JSON shape, the rule that a bad grade still lets the build continue
— is course policy.  Nothing here is useful to someone building hardware who is
not also teaching this class.

Three facts about ``BuildDag`` shape everything below; each is load-bearing.

1. **The DAG halts on the first failed step.**  So a low score must never raise.
   Grading failure and build failure are different things: the first is the
   point of the exercise, the second means the next step has nothing to read.
   :meth:`GradedStep.evaluate` should therefore catch the student's own errors
   and score them — :meth:`Checks.attempt` exists for exactly that.  An
   exception that escapes ``evaluate()`` is taken to mean the step could not
   produce its outputs, and does halt.

2. **A fresh step does not run.**  Freshness is decided from file mtimes before
   any step body executes, so on a second identical invocation ``evaluate()`` is
   never called.  This is why the score is written to disk rather than merely
   printed: the record survives the skip, and ``--grades`` reads it back.

3. **Everything in ``produces`` must be returned** or the DAG raises.  The eval
   record is in ``produces``, so it is written even on the failure path.
"""
from __future__ import annotations

import json
import shutil
import time
import traceback
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Iterator, Sequence

from waveflow.build.build import BuildConfig, BuildStep

__all__ = [
    "Check", "Checks", "GradeResult", "GradedStep", "GradeReportStep", "StudentSourceStep",
    "read_eval", "format_eval", "print_grade_summary", "run_graded_dag_cli",
]

#: Where eval records go, relative to the build root.  ``*.json`` is already in
#: .gitignore, so these stay out of the repository without a new rule.
EVAL_DIR = Path("eval")


# ---------------------------------------------------------------------------
# Checks — the accumulator every evaluate() body is written against
# ---------------------------------------------------------------------------

@dataclass
class Check:
    """One graded assertion: what was worth what, and what to tell the student."""

    name: str
    points: float
    max_points: float
    note: str = ""

    @property
    def passed(self) -> bool:
        return self.points >= self.max_points

    def line(self) -> str:
        """The feedback bullet, e.g. ``✗ (0/5) Values are uniform — chi2 p=0.001``.

        Partial credit gets its own mark: ``18/20`` under a ✗ reads as a
        failure the student cannot see the credit in.
        """
        mark = "✓" if self.passed else ("✗" if self.points <= 0 else "~")
        body = f"{mark} ({_num(self.points)}/{_num(self.max_points)}) {self.name}"
        return f"{body} — {self.note}" if self.note else body


class Checks:
    """Accumulates :class:`Check`\\ s, then hands back a :class:`GradeResult`.

    Every existing lab autograder in this repository re-implements this by hand
    (``score = 0; feedback = ""``; see ``labs/subc/submit.py``), and each one
    invents its own way to weight a partial result.  Doing it once means the
    denominators cannot drift apart from the points a step declares.

    Typical body::

        checks = Checks()
        checks.that(values.max() < 2**W, 3, "PRNG values are in range",
                    f"{n_bad} values exceeded {2**W}")
        checks.fraction(passed.mean(), 5, "Values are uniform",
                        f"chi-square p = {p:.3g}")
        return checks.result()
    """

    def __init__(self) -> None:
        self.checks: list[Check] = []
        self.notes: list[str] = []

    def that(self, ok: bool, points: float, name: str, note: str = "") -> bool:
        """Award *points* if *ok*, otherwise zero.  Returns *ok*, so it can gate.

        *note* is shown only on failure — it is the diagnosis, and a passing
        check has nothing to diagnose.
        """
        ok = bool(ok)
        self.checks.append(Check(name, points if ok else 0.0, points,
                                 "" if ok else note))
        return ok

    def fraction(self, frac: float, points: float, name: str, note: str = "") -> float:
        """Award *frac* of *points* — for "how many of the vectors passed".

        *frac* is clamped to ``[0, 1]``; *note* is shown whenever it is short of
        full marks.
        """
        frac = min(1.0, max(0.0, float(frac)))
        self.checks.append(Check(name, round(frac * points, 3), points,
                                 "" if frac >= 1.0 else note))
        return frac

    def zero(self, points: float, name: str, note: str) -> None:
        """Record a check that could not even be attempted.  Always worth zero."""
        self.checks.append(Check(name, 0.0, points, note))

    @contextmanager
    def attempt(self, points: float, name: str) -> Iterator[None]:
        """Run student code, scoring an exception as a failed check rather than a crash.

        This is the boundary between the two kinds of failure in fact 1 above.
        Inside the block the student's code may raise anything; outside it, an
        exception means the *step* is broken.  Without this, a stray
        ``IndexError`` in a submission would halt the whole build and the
        student would see a traceback instead of a grade.
        """
        try:
            yield
        except Exception as exc:  # noqa: BLE001 — deliberate: any student error is a zero
            self.checks.append(Check(name, 0.0, points,
                                     f"raised {type(exc).__name__}: {exc}"))
        else:
            self.checks.append(Check(name, points, points))

    def note(self, message: str) -> None:
        """Add a feedback line worth no points — context, not credit."""
        self.notes.append(message)

    def result(self, **artifacts: Any) -> GradeResult:
        """Freeze the accumulated checks into a :class:`GradeResult`."""
        return GradeResult(
            score=sum(c.points for c in self.checks),
            max_score=sum(c.max_points for c in self.checks),
            feedback=[c.line() for c in self.checks] + list(self.notes),
            checks=list(self.checks),
            artifacts=artifacts,
        )


# ---------------------------------------------------------------------------
# GradeResult
# ---------------------------------------------------------------------------

@dataclass
class GradeResult:
    """What :meth:`GradedStep.evaluate` returns.

    ``artifacts`` carries the step's *real* outputs (vectors, reports) alongside
    the grade, so one node can both build and grade — the two are the same act
    from the student's side, and splitting them would double the node count for
    no gain.

    ``max_score`` is optional: when ``None`` the step's declared ``points`` is
    used.  When set (as :meth:`Checks.result` does) it must agree with
    ``points``, which is what stops a step's checks from silently summing to a
    different total than the syllabus says it is worth.
    """

    score: float
    max_score: float | None = None
    feedback: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# GradedStep
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class GradedStep(BuildStep):
    """A DAG node that produces something and scores it.

    Subclasses declare:

    * ``points`` — what the step is worth.  A *class* attribute, not a return
      value, because the eval record has to be writable as ``0/points`` when
      ``evaluate()`` never returns at all.  It also means a lab's total is
      known without running anything.
    * ``outputs`` — the step's real file artifacts, exactly as ``produces``
      would normally declare them.  The eval record is added automatically.
    * ``title`` — the human name Gradescope shows.  Defaults to the step name.
    * ``evaluate()`` — the work and the grading.

    ``produces`` is a property here (as in ``SourceStep``) because the eval
    path is derived from the instance's own name, which a ClassVar cannot see.
    """

    points: ClassVar[float] = 0.0
    outputs: ClassVar[dict] = {}

    title: str = ""
    eval_dir: Path = EVAL_DIR
    verbose: bool = True
    #: The :class:`StudentSourceStep`\ s whose files this stage grades.  When
    #: *every* one is still byte-identical to its template, the stage reports
    #: "not started" rather than a list of failed checks.  Leave empty to grade
    #: unconditionally.
    starts_from: Sequence["StudentSourceStep"] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.title:
            self.title = self.name

    @property
    def eval_artifact(self) -> str:
        """Name of this step's eval artifact — unique because step names are."""
        return f"{self.name}_eval"

    @property
    def eval_path(self) -> Path:
        return self.eval_dir / f"{self.name}.json"

    @property
    def produces(self) -> dict:  # type: ignore[override]
        return {self.eval_artifact: self.eval_path, **self.outputs}

    def evaluate(self, config: BuildConfig, **kwargs) -> GradeResult:
        """Do the step's work and grade it.

        ``kwargs`` holds the consumed artifacts and resolved params, exactly as
        for :meth:`BuildStep.run`.  Return a :class:`GradeResult` whose
        ``artifacts`` covers every name in ``outputs``.

        Catch the student's errors in here (see :meth:`Checks.attempt`).  An
        exception raised out of this method is read as "the step could not
        produce its outputs" and halts the build.
        """
        raise NotImplementedError

    def run(self, config: BuildConfig, **kwargs) -> dict[str, Any]:
        """Final — the invariant is that an eval record is always written.

        Subclasses override :meth:`evaluate`.  Overriding this instead would
        let a step fail without leaving a record, and the report step would
        then quietly omit it from the total rather than scoring it zero.
        """
        try:
            result = self.evaluate(config, **kwargs)
        except Exception as exc:  # noqa: BLE001 — re-raised below, after the record lands
            self._write_eval(
                config,
                GradeResult(0.0, self.points,
                            [f"✗ (0/{_num(self.points)}) {self.title} — "
                             f"the step did not complete: {type(exc).__name__}: {exc}"]),
                error=traceback.format_exc(),
            )
            raise

        declared, reported = float(self.points), result.max_score
        if reported is not None and abs(reported - declared) > 1e-9:
            raise RuntimeError(
                f"Step '{self.name}' declares points={_num(declared)} but its checks total "
                f"{_num(reported)}. Fix one or the other — a mismatch means the grade "
                f"a student sees is not the grade the lab is worth.")
        result.max_score = declared
        result.score = min(declared, max(0.0, float(result.score)))

        # A stage whose files are all still the shipped template has not been
        # attempted, and saying so is not the same as listing failed checks.
        # Without this, a student's very first run reports a page of ✗ marks for
        # work they have not had a chance to do yet — a failing grade as the
        # opening move, when nothing has gone wrong at all.
        #
        # `evaluate()` still ran: it produced the declared artifacts, so the DAG
        # stays intact and the later stages have something to read.  Only what
        # the student is told changes, and the score goes to zero, which is more
        # honest than the partial credit the vacuous checks would have paid.
        if self.starts_from and all(s.is_untouched(config) for s in self.starts_from):
            names = [str(s.path) for s in self.starts_from]
            files = names[0] if len(names) == 1 else (
                ", ".join(names[:-1]) + f" and {names[-1]}")
            is_are, it_them = ("is", "it") if len(names) == 1 else ("are", "them")
            result = GradeResult(
                0.0, declared,
                [f"· (0/{_num(declared)}) not started — {files} {is_are} still "
                 f"unchanged from the template.",
                 f"    Open {it_them}, look for the TODO comments, and run this again."],
                artifacts=result.artifacts)

        record = self._write_eval(config, result)
        if self.verbose:
            print(format_eval(record, indent="    "))

        missing = [k for k in self.outputs if k not in result.artifacts]
        if missing:
            raise RuntimeError(
                f"Step '{self.name}' declared {missing} in outputs but evaluate() "
                f"did not return them.")
        return {self.eval_artifact: record["path"], **result.artifacts}

    def _write_eval(self, config: BuildConfig, result: GradeResult,
                    *, error: str | None = None) -> dict[str, Any]:
        path = config.root_dir / self.eval_path
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "step": self.name,
            "title": self.title,
            "score": round(float(result.score), 3),
            "max_score": float(result.max_score if result.max_score is not None else self.points),
            "feedback": list(result.feedback),
            "checks": [vars(c) for c in result.checks],
            "error": error,
            "timestamp": time.time(),
        }
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        record["path"] = path
        return record


# ---------------------------------------------------------------------------
# StudentSourceStep — the file the student edits
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class StudentSourceStep(BuildStep):
    """A source file the student completes, seeded from ``partial/`` on first use.

    ``labkit`` publishes redacted files into ``partial/`` rather than at the top
    level so that ``git pull`` cannot overwrite work in progress.  The cost is a
    manual "copy the files up first" step, which students forget and which then
    surfaces as a missing-file traceback rather than as instructions.

    This step closes that: when the top-level file is absent and the ``partial/``
    one exists, it copies it up and says so.  **It never overwrites** — once the
    student's file exists, this step only checks that it still does.

    Otherwise it behaves as ``SourceStep``: the file is a root artifact, and its
    mtime is what makes everything downstream rebuild when the student edits it.
    """

    description = "A source file the student completes."
    params: ClassVar[dict] = {}

    artifact: str
    path: Path
    partial: Path | None = None

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        if self.partial is None:
            self.partial = Path("partial") / self.path
        self.partial = Path(self.partial)
        super().__post_init__()

    def _default_name(self) -> str:
        return self.artifact

    @property
    def produces(self) -> dict:  # type: ignore[override]
        return {self.artifact: self.path}

    def expected_paths(self, config: BuildConfig) -> dict[str, Path]:
        return {self.artifact: self._resolved(config)}

    def is_untouched(self, config: BuildConfig) -> bool:
        """True when the student's file is still byte-identical to its template.

        This is how a graded stage tells "not attempted" from "attempted and
        wrong" — two things that deserve very different messages and that a
        score alone cannot distinguish.

        Returns ``False`` whenever the comparison cannot be made (no template,
        no file), because the safe default is to grade normally rather than to
        excuse work that may well have been done.
        """
        target = self._resolved(config)
        seed = Path(config.root_dir) / self.partial
        if not (target.exists() and seed.exists()):
            return False
        return target.read_bytes() == seed.read_bytes()

    def _resolved(self, config: BuildConfig) -> Path:
        return self.path if self.path.is_absolute() else Path(config.root_dir) / self.path

    def run(self, config: BuildConfig, **_) -> dict[str, Any]:
        target = self._resolved(config)
        if not target.exists():
            seed = Path(config.root_dir) / self.partial
            if not seed.exists():
                raise RuntimeError(
                    f"{self.path} is missing, and there is no template at {self.partial} "
                    f"to start from. Re-pull the lab, or check you are running the build "
                    f"from the lab directory.")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(seed, target)
            print(f"    STARTED {self.path} from {self.partial} — edit {self.path}, "
                  f"not the copy in partial/.")
        return {self.artifact: target}


# ---------------------------------------------------------------------------
# GradeReportStep — the terminal node
# ---------------------------------------------------------------------------

@dataclass(kw_only=True)
class GradeReportStep(BuildStep):
    """Collect every graded step's record into the Gradescope submission.

    A DAG node rather than the separate ``submit.py`` the older labs use, so
    the eval records it bundles cannot be stale: they are its consumed
    artifacts, and freshness is what the DAG is for.  A student who edits their
    source and runs ``python prng_build.py`` re-grades and re-bundles in one
    command; there is no second script whose omission silently uploads
    yesterday's score.

    ``bundle`` lists the source files Gradescope requires alongside the results
    — the same list that goes in ``autograder_config.xml``.  Paths are relative
    to the build root.
    """

    description = "Collect the graded steps into submitted_results.json and submission.zip."
    params: ClassVar[dict] = {}

    graded: Sequence[GradedStep] = ()
    bundle: Sequence[Path] = ()
    submit_dir: Path = Path("submission")

    def __post_init__(self) -> None:
        super().__post_init__()
        self.consumes = [s.eval_artifact for s in self.graded]

    @property
    def produces(self) -> dict:  # type: ignore[override]
        return {"submitted_results": self.submit_dir / "submitted_results.json",
                "submission_zip": self.submit_dir / "submission.zip"}

    def run(self, config: BuildConfig, **kwargs) -> dict[str, Any]:
        root = Path(config.root_dir)
        # A step with no record scores zero rather than blocking the submission.
        # Refusing to build the zip would punish a student twice for the same
        # unfinished stage, and would take away the partial work they do have.
        records = [_eval_or_zero(root / s.eval_path, s) for s in self.graded]

        # The shape gradescope/autograde.py copies straight through to
        # /autograder/results/results.json -- do not restructure it here.
        results = {
            "score": round(sum(r["score"] for r in records), 3),
            "tests": [{"name": r["title"], "score": r["score"],
                       "max_score": r["max_score"],
                       "output": "\n".join(r["feedback"])} for r in records],
        }

        out = root / self.submit_dir
        out.mkdir(parents=True, exist_ok=True)
        results_path = out / "submitted_results.json"
        results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

        missing = [p for p in self.bundle if not (root / p).exists()]
        if missing:
            raise RuntimeError(
                f"Cannot build the submission: required file(s) not found: "
                f"{', '.join(str(p) for p in missing)}")

        zip_path = out / "submission.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(results_path, arcname="submitted_results.json")
            for rel in self.bundle:
                zf.write(root / rel, arcname=Path(rel).name)

        total, possible = results["score"], sum(r["max_score"] for r in records)
        print(f"    TOTAL {_num(total)}/{_num(possible)}")
        for record in records:
            print(format_eval(record, indent="    "))
        print(f"    upload {zip_path.relative_to(root)} to Gradescope")
        return {"submitted_results": results_path, "submission_zip": zip_path}


# ---------------------------------------------------------------------------
# Reading records back — the path that survives a skipped step
# ---------------------------------------------------------------------------

def _eval_or_zero(path: Path, step: GradedStep) -> dict[str, Any]:
    """The step's record, or a zero for a stage that was never run."""
    if Path(path).exists():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return {"step": step.name, "title": step.title, "score": 0.0,
            "max_score": float(step.points), "checks": [], "error": None,
            "feedback": [f"✗ (0/{_num(step.points)}) {step.title} — not run. "
                         f"Run `--through {step.name}` before submitting."]}


def read_eval(path: Path) -> dict[str, Any]:
    """Load one eval record, with a message a student can act on if it is absent."""
    path = Path(path)
    if not path.exists():
        raise RuntimeError(
            f"No evaluation found at {path} — run the step that produces it first.")
    return json.loads(path.read_text(encoding="utf-8"))


def format_eval(record: dict[str, Any], indent: str = "") -> str:
    """Render one record as the score line plus its feedback bullets."""
    head = f"{record['title']}: {_num(record['score'])}/{_num(record['max_score'])}"
    lines = [indent + head] + [f"{indent}  {line}" for line in record["feedback"]]
    return "\n".join(lines)


def print_grade_summary(root_dir: Path, steps: Sequence[GradedStep]) -> None:
    """Print every graded step's last recorded score, running nothing.

    Fact 2 above is why this exists: an up-to-date step is skipped, so a second
    ``--through prng_sim`` prints ``UP-TO-DATE`` and no grade.  Reading the
    records back gives the student their standing at any time.
    """
    root, total, possible = Path(root_dir), 0.0, 0.0
    for step in steps:
        path = root / step.eval_path
        possible += float(step.points)
        if not path.exists():
            print(f"{step.title}: —/{_num(step.points)}  (not yet run)")
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        total += record["score"]
        print(format_eval(record))
    print(f"\nTOTAL {_num(total)}/{_num(possible)}")


def run_graded_dag_cli(dag_factory, *, root_dir: Path, graded_steps, **kwargs) -> None:
    """``run_dag_cli`` plus a ``--grades`` flag that reports without building.

    ``--grades`` is handled before argparse rather than through ``extra_args``
    because ``run_dag_cli`` has no post-parse hook to short-circuit on: its
    knobs all feed ``BuildConfig.params``, and this one has to print and exit.
    Kept to this one pre-check so waveflow needs no change.

    ``graded_steps`` is a zero-arg callable returning the lab's graded steps in
    report order.
    """
    import sys

    from waveflow.build.cli import run_dag_cli

    if "--grades" in sys.argv:
        print_grade_summary(root_dir, graded_steps())
        return
    run_dag_cli(dag_factory, root_dir=root_dir, **kwargs)


def _num(value: float) -> str:
    """Format a score: ``5`` not ``5.0``, but ``2.5`` when it really is a half."""
    return str(int(value)) if float(value).is_integer() else f"{value:g}"
