"""prng — the Unit 1 lab build.

Three graded stages, run one at a time::

    python prng_build.py --list-steps-verbose   # what the stages are
    python prng_build.py --through pysim        # generate the stream, scored
    python prng_build.py --through pyeval       # measure it, scored
    python prng_build.py --through svsim        # the SystemVerilog, scored
    python prng_build.py                        # everything, then the submission zip
    python prng_build.py --grades               # your scores, without rebuilding

``pysim`` runs your Python LFSR and asks only whether the stream is well formed.
``pyeval`` runs the measuring code *you* wrote over that stream and asks two
different questions of each measurement: is your measurement right, and is the
generator any good?  ``svsim`` then runs your SystemVerilog and checks it
against your Python model, sample for sample.

The order is the point.  You find out whether the design works while it is still
Python, where a fix costs an edit — not after it is hardware, where it costs a
day.

YOU DO NOT NEED TO EDIT THIS FILE.  Your work goes in ``prng_model.py``,
``prng_eval.py``, ``prng_next.sv`` and ``tb_prng.sv``.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from waveflow.build.build import BuildConfig, BuildDag, SourceStep

from hwdesign.grading import (
    Checks, GradeReportStep, GradedStep, GradeResult, StudentSourceStep,
    run_graded_dag_cli,
)

_SOURCE_DIR = Path(__file__).resolve().parent

# The lab's specification.  These live here rather than in prng_model.py so that
# the grader and the simulator agree on them no matter what a submission does to
# its own constants — and so that a file which fails to import at all can still
# be scored against the right numbers instead of crashing the build.
NSAMP = 1000     # samples to generate
BITS = 8         # bits per sample
SEED = 0xB0BA    # nonzero: zero is a fixed point of the recurrence

#: Bins for the histogram.  Sixteen over 256 values gives ~62 samples per bin at
#: n=1000 — enough for a real bias to show, where one bin per value would average
#: four and drown in noise.
NBINS = 16

#: How many standard errors of lag-1 correlation to allow.  Expressed in sigma
#: rather than as a bare number so that it stays meaningful if NSAMP changes:
#: the standard error of a correlation over n samples is 1/sqrt(n), which is
#: 0.032 at n=1000, so this is a threshold of about 0.16.
#:
#: Measured behaviour at n=1000, which is what sets the value: a correct
#: implementation lands around 0.02 sigma with this seed, one step per sample
#: gives 15 sigma, and two steps gives 7.6.  Five leaves the correct answer an
#: enormous margin while still failing every gross error.
CORR_SIGMA_MAX = 5.0

#: How far a histogram bin may sit from the flat line, as a fraction of it.
#: Poisson noise alone is worth about 38% at three sigma with these bin counts,
#: so anything much tighter would fail correct work.  A correct stream measures
#: about 20% with this seed.
FLAT_TOL = 0.45

#: How closely a student's own measurement must match the true value for their
#: measuring code to count as correct.
CORR_TOL = 1e-6


def load_student_module(source_dir: Path, name: str):
    """Import one of the student's modules by path, fresh, whatever the working directory.

    By path rather than by name because the lab is a directory of scripts, not an
    installed package — and freshly each time so that a rebuild in the same
    process picks up an edit instead of a cached module.
    """
    path = Path(source_dir) / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Stage 1 — the Python model
# ---------------------------------------------------------------------------

def check_samples(samples: np.ndarray, nsamp: int, bits: int) -> Checks:
    """Score a generated stream on its own terms.  No reference sequence involved.

    This stage asks only whether the stream is *well formed* — the right number
    of values, of the right width, actually varying.  Whether it is any good is
    the next stage's question, and it is the student who answers it there.

    Any correct PRNG passes.  The lab pins one algorithm in the write-up so
    nobody has to guess, but the grading asks whether the numbers are right, not
    whether they came from a particular recurrence.
    """
    checks = Checks()
    hi = (1 << bits) - 1
    range_label = f"Values are in range 0 to {hi}"
    vary_label = "The generator does not get stuck"

    checks.that(len(samples) >= nsamp, 4, f"Generated at least {nsamp} samples",
                f"got {len(samples)}")

    if len(samples) == 0:
        checks.zero(3, range_label, "no samples to check")
        checks.zero(3, vary_label, "no samples to check")
        return checks

    n_bad = int(((samples < 0) | (samples > hi)).sum())
    checks.that(n_bad == 0, 3, range_label,
                f"{n_bad} of {len(samples)} values fell outside — the smallest was "
                f"{int(samples.min())}, the largest {int(samples.max())}")

    # Being in range is not enough on its own.  A generator stuck at a single
    # value — which is what the unedited stub produces — satisfies it vacuously,
    # so "it moves at all" has to be asked separately.
    n_unique = int(np.unique(samples).size)
    checks.that(n_unique > 1, 3, vary_label,
                f"every sample is {int(samples[0])} — the state is not advancing")
    return checks


@dataclass(kw_only=True)
class PySimStep(GradedStep):
    description = "Run your Python LFSR and check the numbers it produces."
    points = 10.0
    outputs = {"py_samples": Path("vectors/prng_py.csv")}
    consumes = ["prng_model_src"]

    def evaluate(self, config: BuildConfig, **_) -> GradeResult:
        root = Path(config.root_dir)
        vectors = root / "vectors/prng_py.csv"
        samples = np.zeros(0, dtype=np.int64)
        failure = ""

        # Importing is inside the try as well: a file with a syntax error cannot
        # be loaded at all, and that has to score zero rather than take the build
        # down and leave you with no submission.
        try:
            model = load_student_module(root, "prng_model")
            samples = np.asarray(model.lfsr_stream(SEED, NSAMP), dtype=np.int64)
        except Exception as exc:  # noqa: BLE001 — any student error is a zero, not a crash
            failure = f"prng_model.py raised {type(exc).__name__}: {exc}"

        # Written even when nothing was generated, so the next stage has a file
        # to compare against and can report a score instead of failing on a
        # missing input.
        vectors.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"x": samples}).to_csv(vectors, index=False)

        checks = check_samples(samples, NSAMP, BITS)
        if failure:
            checks.note(failure)
        return checks.result(py_samples=vectors)


# ---------------------------------------------------------------------------
# Stage 2 — evaluating the stream, before any hardware exists
# ---------------------------------------------------------------------------

def check_evaluation(samples: np.ndarray, reported_corr: float,
                     reported_counts: np.ndarray, bits: int) -> Checks:
    """Score the student's own measurements against the truth, and the design against both.

    Each measurement is worth two things, and they are different questions:
    *can you measure it* (the code) and *is the answer good* (the design).  A
    correct measurement of a bad generator earns the first and not the second,
    which is exactly the distinction this stage exists to teach.

    The weight goes to whichever check actually discriminates.  The correlation
    *result* is a sharp instrument — a generator that steps once per sample
    instead of eight lands sixteen standard errors out — so it carries three.
    Histogram flatness is a blunt one at this sample size, since Poisson noise
    alone is worth most of the tolerance, so it carries one.  The two points
    freed by that go to producing the figure, which is scored in
    :meth:`PyEvalStep.evaluate` because it is about a file rather than a number.
    """
    checks = Checks()
    hi = (1 << bits) - 1
    n = len(samples)

    # --- the lag-1 correlation ------------------------------------------------
    if n < 3 or int(np.unique(samples).size) <= 1:
        # A constant stream has zero variance, so the true correlation is 0/0.
        # Calling that "uncorrelated" would pass the most predictable sequence
        # there is.
        checks.zero(2, "Your lag-1 correlation is correct",
                    "there is no usable stream to measure — fix prng_model.py first")
        checks.zero(3, "Successive samples are uncorrelated",
                    "every sample is identical, so each one predicts the next exactly")
    else:
        true_corr = float(np.corrcoef(samples[:-1], samples[1:])[0, 1])
        checks.that(abs(reported_corr - true_corr) <= CORR_TOL, 2,
                    "Your lag-1 correlation is correct",
                    f"you reported {reported_corr:+.6f}; the true value is {true_corr:+.6f}")

        # Judged in standard errors, not raw magnitude, so the bar stays
        # meaningful if the sample count ever changes.
        sigma = 1.0 / np.sqrt(n)
        z = abs(true_corr) / sigma
        checks.that(z < CORR_SIGMA_MAX, 3, "Successive samples are uncorrelated",
                    f"lag-1 correlation = {true_corr:+.4f}, which is {z:.1f} standard "
                    f"errors from zero — each sample predicts the next far too well")

    # --- the histogram --------------------------------------------------------
    true_counts, _ = np.histogram(np.clip(samples, 0, hi), bins=NBINS, range=(0, hi + 1))
    reported = np.asarray(reported_counts).ravel()

    if reported.shape != true_counts.shape:
        checks.zero(2, "Your histogram is correct",
                    f"you returned {reported.size} bins; {NBINS} were asked for")
    else:
        wrong = int((reported != true_counts).sum())
        first = int(np.flatnonzero(reported != true_counts)[0]) if wrong else 0
        checks.that(wrong == 0, 2, "Your histogram is correct",
                    f"{wrong} of {NBINS} bins are wrong; the first is bin {first}, "
                    f"where you counted {int(reported[first])} and the true count is "
                    f"{int(true_counts[first])}")

    if n == 0:
        checks.zero(1, "The histogram is flat", "no samples to check")
    else:
        expected = n / NBINS
        dev = float(np.abs(true_counts - expected).max() / expected)
        checks.that(dev <= FLAT_TOL, 1, "The histogram is flat",
                    f"the worst bin is {dev:.0%} away from the flat line of "
                    f"{expected:.0f}, past the {FLAT_TOL:.0%} allowed")
    return checks


@dataclass(kw_only=True)
class PyEvalStep(GradedStep):
    description = "Measure your stream — is it actually random? — before building any hardware."
    points = 10.0
    outputs = {"eval_figure": Path("results/prng_hist.png")}
    consumes = ["prng_eval_src", "py_samples"]

    def evaluate(self, config: BuildConfig, py_samples: Path, **_) -> GradeResult:
        root = Path(config.root_dir)
        samples = pd.read_csv(py_samples)["x"].to_numpy(dtype=np.int64)

        corr, counts, failure = 0.0, np.zeros(NBINS, dtype=int), ""
        try:
            ev = load_student_module(root, "prng_eval")
            corr = float(ev.lag1_correlation(samples))
            counts = np.asarray(ev.histogram(samples, NBINS, 1 << BITS))
        except Exception as exc:  # noqa: BLE001 — any student error is a zero, not a crash
            failure = f"prng_eval.py raised {type(exc).__name__}: {exc}"

        checks = check_evaluation(samples, corr, counts, BITS)
        if failure:
            checks.note(failure)

        # The figure plots the counts the student computed, not a recomputed
        # set, so a wrong histogram is visible rather than hidden by the plot.
        #
        # Only its *existence* is scored.  Judging a plot mechanically is a poor
        # trade — the checks that could be automated are the ones a student can
        # satisfy without drawing anything worth looking at — so the file goes
        # into the submission instead, where it can be read by a person who
        # wants to.
        figure = root / "results/prng_hist.png"
        # Removed first, so that a figure left over from an earlier run cannot
        # earn the point for code that no longer draws one.
        figure.unlink(missing_ok=True)
        try:
            ev = load_student_module(root, "prng_eval")
            ev.plot_evaluation(samples, counts, corr, BITS, figure)
        except Exception as exc:  # noqa: BLE001 — a broken plot costs its own points, no more
            checks.note(f"plot_evaluation raised {type(exc).__name__}: {exc}")

        drew = figure.exists() and figure.stat().st_size > 0
        checks.that(drew, 2, "You produced a histogram figure",
                    f"no figure was written to {figure.name} — plot_evaluation must "
                    f"save one, and it is part of what you submit")
        if not drew:
            # The artifact is declared, so something has to be there for the
            # submission step to bundle.  A placeholder says plainly that no
            # plot was drawn rather than leaving a confusing gap.
            _placeholder_figure(figure)

        result = checks.result(eval_figure=figure)
        result.feedback.append(f"  histogram written to {figure.relative_to(root)}")
        return result


def _placeholder_figure(path: Path) -> None:
    """A stand-in PNG, so the declared artifact exists when no plot was drawn.

    Deliberately built with ``plt.figure`` rather than ``plt.subplots``: the
    latter line is byte-identical to one inside a solution block in
    ``prng_eval.py``, and labkit's leak guard — rightly — cannot tell generic
    matplotlib boilerplate from a leaked answer.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(7.5, 4))
    fig.text(0.5, 0.5, "no histogram was drawn", ha="center", va="center",
             color="0.4")
    fig.savefig(path, dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Stage 3 — the SystemVerilog
# ---------------------------------------------------------------------------

def compare_streams(py_path: Path, sv_path: Path) -> tuple[float, str]:
    """Return ``(fraction matching, note)`` for two one-column sample CSVs."""
    py = pd.read_csv(py_path)["x"].to_numpy(dtype=np.int64)
    sv = pd.read_csv(sv_path)["x"].to_numpy(dtype=np.int64)

    if len(py) == 0:
        return 0.0, "your Python model produced no samples, so there is nothing to match"

    # Consistency between two languages is only evidence when there is something
    # to be consistent about.  Both unedited stubs return zero, so they agree
    # perfectly while implementing nothing — this is the check that stops an
    # untouched submission from collecting full marks here.
    if np.unique(py).size <= 1:
        return 0.0, ("your Python model produced the same value every time, so a "
                     "matching simulation proves nothing — fix prng_model.py first")

    if len(sv) != len(py):
        return 0.0, (f"the simulation wrote {len(sv)} samples but your Python model "
                     f"produced {len(py)}")

    same = py == sv
    frac = float(same.mean())
    if frac == 1.0:
        return 1.0, ""

    first = int(np.flatnonzero(~same)[0])
    return frac, (f"{int((~same).sum())} of {len(py)} samples differ; the first is "
                  f"sample {first}, where Python says {py[first]} and the "
                  f"simulation says {sv[first]}")


@dataclass(kw_only=True)
class SvSimStep(GradedStep):
    description = "Simulate your SystemVerilog LFSR and compare it with your Python model."
    points = 10.0
    consumes = ["prng_next_src", "prng_tb_src", "py_samples"]

    def evaluate(self, config: BuildConfig, **_) -> GradeResult:
        from waveflow.scripts.sv_sim import SvSimError, run_sv_sim

        root = Path(config.root_dir)
        checks = Checks()
        label = "SystemVerilog matches your Python model"

        # The simulation is run here rather than by a separate SvSimStep so that
        # a compile error becomes a scored zero with the tool output attached.
        # As its own DAG node it would raise, halt the build, and leave you with
        # a traceback and no submission file.
        try:
            run_sv_sim(
                [root / "prng_next.sv"], root / "tb_prng.sv",
                sim_dir=root / "sim/prng",
                plusargs={"vecdir": root / "vectors",
                          "nsamp": str(NSAMP), "seed": str(SEED)},
                capture_output=True,
            )
        except SvSimError as exc:
            checks.zero(self.points, label,
                        f"the simulation did not run: {exc}".rstrip())
            return checks.result()

        sv_path = root / "vectors/prng_sv.csv"
        if not sv_path.exists():
            checks.zero(self.points, label,
                        "the simulation finished but wrote no output file")
            return checks.result()

        frac, note = compare_streams(root / "vectors/prng_py.csv", sv_path)
        checks.fraction(frac, self.points, label, note)
        return checks.result()


# ---------------------------------------------------------------------------
# The graph
# ---------------------------------------------------------------------------

def lab_steps() -> tuple[list[StudentSourceStep], list[GradedStep]]:
    """The student's four files, and the three stages that grade them.

    Built together because each stage needs to know which files are *its* — a
    stage whose files are all still the shipped template reports "not started"
    instead of a page of failed checks.
    """
    model_src = StudentSourceStep(artifact="prng_model_src", path=Path("prng_model.py"))
    eval_src = StudentSourceStep(artifact="prng_eval_src", path=Path("prng_eval.py"))
    # The testbench is a student file too: the loop that turns single-bit steps
    # into whole samples lives there.
    next_src = StudentSourceStep(artifact="prng_next_src", path=Path("prng_next.sv"))
    tb_src = StudentSourceStep(artifact="prng_tb_src", path=Path("tb_prng.sv"))

    return ([model_src, eval_src, next_src, tb_src],
            [PySimStep(name="pysim", title="Python LFSR model",
                       starts_from=[model_src]),
             PyEvalStep(name="pyeval", title="Evaluating the generator",
                        starts_from=[eval_src]),
             SvSimStep(name="svsim", title="SystemVerilog LFSR",
                       starts_from=[next_src, tb_src])])


def graded_steps() -> list[GradedStep]:
    """The graded stages, in the order the submission reports them."""
    return lab_steps()[1]


def build_prng_dag() -> BuildDag:
    dag = BuildDag()
    (model_src, eval_src, next_src, tb_src), (pysim, pyeval, svsim) = lab_steps()

    dag.add(model_src)
    dag.add(pysim)

    dag.add(eval_src)
    dag.add(pyeval)

    dag.add(next_src)
    dag.add(tb_src)
    dag.add(svsim)

    # svsim does not consume pyeval's output, and no edge pretends otherwise —
    # the reason to evaluate before building hardware is a habit, not a data
    # dependency, and a DAG that lies about its dependencies is worth less than
    # the lesson.
    dag.add(GradeReportStep(
        name="submit", graded=[pysim, pyeval, svsim],
        # The histogram goes in the zip so it can be looked at afterwards.  It is
        # the one part of this lab whose quality a person can judge in a second
        # and a script cannot judge at all.
        bundle=[Path("prng_model.py"), Path("prng_eval.py"), Path("prng_next.sv"),
                Path("tb_prng.sv"), Path("vectors/prng_py.csv"),
                Path("results/prng_hist.png")]))
    return dag


def main() -> None:
    run_graded_dag_cli(
        build_prng_dag,
        graded_steps=graded_steps,
        description="prng — Unit 1 lab: a linear-feedback shift register.",
        default_through="submit",
        root_dir=_SOURCE_DIR,
    )


if __name__ == "__main__":
    main()
