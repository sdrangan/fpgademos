---
title: Autograders and Gradescope
parent: Instructor Guide
nav_order: 3
has_children: false
---

# Autograders and Gradescope

Grading is part of the build. A lab is a `BuildDag` whose nodes are
`GradedStep`s, and each one does its stage's real work *and* scores it. There is
no separate grading script to remember to run, and no way for a student to
upload a score that does not match the code they just built.

```
prng_build.py
    StudentSourceStep   prng_model.py, prng_eval.py, prng_next.sv, tb_prng.sv
        │
    GradedStep  pysim     10 pts  →  eval/pysim.json
    GradedStep  pyeval    10 pts  →  eval/pyeval.json
    GradedStep  svsim     10 pts  →  eval/svsim.json
        │
    GradeReportStep       submission/submitted_results.json
                          submission/submission.zip     ← the student uploads this
```

The student runs `python prng_build.py`; the zip appears; they upload it. On
Gradescope, `gradescope/autograde.py` checks that the required files are present
and copies `submitted_results.json` straight through to
`/autograder/results/results.json`. It computes nothing.

Everything below is in [`hwdesign/grading.py`](../../hwdesign/grading.py), and
every example is real code from
[`labs/prng/prng_build.py`](https://github.com/sdrangan/hwdesign-soln/blob/main/labs/prng/prng_build.py).

---

## Three facts about the DAG

These shape how every graded step is written, so they come first.

**1. The DAG halts on the first failed step, so a low score must never raise.**
Grading failure and build failure are different things. The first is the point
of the exercise; the second means the next step has nothing to read. So
`evaluate()` catches the student's own errors and scores them. An exception that
escapes `evaluate()` is read as "this step could not produce its outputs" and
does halt the build.

**2. A fresh step does not run.** Freshness is decided from file mtimes before
any step body executes, so on a second identical invocation `evaluate()` is
never called. That is why the score is written to disk rather than printed: the
record survives the skip, and `--grades` reads it back.

**3. Everything in `produces` must be returned.** The eval record is in
`produces`, so it is written even on the failure path — including when
`evaluate()` raised.

---

## Writing a graded step

A subclass declares four things:

| | |
|---|---|
| `points` | What the step is worth. A **class** attribute, so a lab's total is known without running anything, and so a step that never returns can still be recorded as `0/points` |
| `outputs` | The step's real file artifacts, exactly as `produces` would declare them. The eval record is added for you |
| `title` | The name Gradescope shows. Defaults to the step name |
| `evaluate()` | The work and the grading, together |

Here is the whole of the prng lab's first stage:

```python
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
        except Exception as exc:
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
```

Two habits worth copying. The `try` covers the *import*, not just the call — a
file with a syntax error cannot be loaded at all, and that has to be a zero
rather than a halted build. And the output file is written even when nothing was
generated, so the next stage reads an empty CSV and reports a score instead of
failing on a missing input.

### The `Checks` accumulator

`evaluate()` bodies are written against `Checks`, which collects assertions and
turns them into a score plus the feedback bullets the student sees.

| Method | Use it for |
|---|---|
| `that(ok, points, name, note)` | A pass/fail assertion. Returns `ok`, so it can gate later work. `note` shows only on failure — it is the diagnosis, and a passing check has nothing to diagnose |
| `fraction(frac, points, name, note)` | "How many of the vectors matched." `frac` is clamped to `[0, 1]`; `note` shows whenever it is short of full marks |
| `zero(points, name, note)` | A check that could not be attempted at all — a simulation that never compiled |
| `attempt(points, name)` | A context manager that runs student code and scores an exception as a failed check rather than a crash. This is the boundary in fact 1 |
| `note(message)` | A feedback line worth no points. Context, not credit |

```python
checks = Checks()
checks.that(values.max() < 2**W, 3, "PRNG values are in range",
            f"{n_bad} values exceeded {2**W}")
checks.fraction(passed.mean(), 5, "Values are uniform",
                f"chi-square p = {p:.3g}")
return checks.result()
```

`result()` produces a `GradeResult`, and its `max_score` is the sum of the
checks' own maxima. Pass the step's artifacts as keyword arguments —
`checks.result(py_samples=vectors)` — so one node can both build and grade.

The feedback a student sees is one line per check, marked by outcome:

```
✓ (4/4) Generated at least 1000 samples
~ (2/3) Successive samples are uncorrelated — lag-1 r = 0.31
✗ (0/3) The generator does not get stuck — 998 of 1000 samples were identical
```

Partial credit gets `~` rather than `✗`, because `18/20` under a cross reads as
a failure the student cannot see the credit in.

### A step that scores a tool failure

When the work is done by an external tool, run it *inside* `evaluate()` so a
compile error becomes a scored zero with the tool's output attached, rather than
a separate DAG node that raises and leaves the student with a traceback and no
submission:

```python
try:
    run_sv_sim(
        [root / "prng_next.sv"], root / "tb_prng.sv",
        sim_dir=root / "sim/prng",
        plusargs={"vecdir": root / "vectors", "nsamp": str(NSAMP), "seed": str(SEED)},
        capture_output=True,
    )
except SvSimError as exc:
    checks.zero(self.points, label, f"the simulation did not run: {exc}".rstrip())
    return checks.result()
```

### Checks are worth what they discriminate

The interesting decision is not the total, it is how the total is split. Weight
each check by how sharply it separates a right answer from a wrong one. From the
prng lab's own reasoning: the lag-1 correlation *result* is a sharp instrument —
a generator that steps once per sample instead of eight lands sixteen standard
errors out — so it carries three points. Histogram flatness is blunt at that
sample size, since Poisson noise alone eats most of the tolerance, so it carries
one.

It is also worth separating *can you measure it* from *is the answer good*. A
correct measurement of a bad generator earns the first and not the second, and
splitting them is often the thing the stage exists to teach.

### `starts_from` — "not started" is not a failing grade

A stage whose files are all still byte-identical to the shipped template has not
been attempted, and saying so is not the same as listing failed checks:

```python
PySimStep(name="pysim", title="Python LFSR model", starts_from=[model_src])
```

```
· (0/10) not started — prng_model.py is still unchanged from the template.
    Open it, look for the TODO comments, and run this again.
```

Without it, a student's very first run reports a page of ✗ marks for work they
have not had a chance to do yet — a failing grade as the opening move, when
nothing has gone wrong. `evaluate()` still runs and still produces its
artifacts, so the DAG stays intact; only what the student is told changes.

### The points must add up

If a step declares `points = 10.0` and its checks total 8, the build raises:

```
Step 'pysim' declares points=10 but its checks total 8. Fix one or the other —
a mismatch means the grade a student sees is not the grade the lab is worth.
```

This is why `points` is declared on the step rather than returned from
`evaluate()`. The syllabus total and the sum of the checks are two independent
statements of the same number, and the build refuses to let them drift.

---

## Wiring the DAG

Build the student's source steps and the graded steps together, so each stage
knows which files are its own:

```python
def lab_steps() -> tuple[list[StudentSourceStep], list[GradedStep]]:
    model_src = StudentSourceStep(artifact="prng_model_src", path=Path("prng_model.py"))
    eval_src  = StudentSourceStep(artifact="prng_eval_src",  path=Path("prng_eval.py"))
    next_src  = StudentSourceStep(artifact="prng_next_src",  path=Path("prng_next.sv"))
    tb_src    = StudentSourceStep(artifact="prng_tb_src",    path=Path("tb_prng.sv"))

    return ([model_src, eval_src, next_src, tb_src],
            [PySimStep(name="pysim",  title="Python LFSR model",      starts_from=[model_src]),
             PyEvalStep(name="pyeval", title="Evaluating the generator", starts_from=[eval_src]),
             SvSimStep(name="svsim",  title="SystemVerilog LFSR",     starts_from=[next_src, tb_src])])
```

Then add them to the DAG and finish with the terminal report node:

```python
dag.add(GradeReportStep(
    name="submit", graded=[pysim, pyeval, svsim],
    bundle=[Path("prng_model.py"), Path("prng_eval.py"), Path("prng_next.sv"),
            Path("tb_prng.sv"), Path("vectors/prng_py.csv"),
            Path("results/prng_hist.png")]))
```

`GradeReportStep` consumes every graded step's eval record, so it *cannot*
bundle a stale score — freshness is what the DAG is for. A step with no record
scores zero rather than blocking the submission: refusing to build the zip would
punish a student twice for one unfinished stage and take away the partial work
they do have.

`bundle` is the list of source files that go in the zip alongside the results.
**Remember its two properties**, because both matter later:

- the zip is **flat** — `arcname=Path(rel).name`, so `vectors/prng_py.csv`
  arrives as `prng_py.csv`;
- it is the same list that goes in `autograder_config.xml`.

Finally, the CLI:

```python
run_graded_dag_cli(
    build_prng_dag, graded_steps=graded_steps,
    description="prng — Unit 1 lab: a linear-feedback shift register.",
    default_through="submit", root_dir=_SOURCE_DIR)
```

which gives the student:

```bash
python prng_build.py --through pysim   # one stage, with its score and why
python prng_build.py                   # everything, then the zip
python prng_build.py --grades          # last recorded scores, running nothing
```

`--grades` exists because of fact 2: an up-to-date step is skipped, so a second
`--through pysim` prints `UP-TO-DATE` and no grade. Reading the records back
gives the student their standing at any time.

---

## Creating the autograder

Two files. One you write, one is generated.

### 1. `autograder_config.xml`

The list of files a submission must contain. It is the **only** check the
autograder performs.

```xml
<autograder>
    <required_files>
        <file>prng_model.py</file>
        <file>prng_eval.py</file>
        <file>prng_next.sv</file>
        <file>tb_prng.sv</file>
        <file>prng_py.csv</file>
        <file>prng_hist.png</file>
    </required_files>
</autograder>
```

Two rules, both consequences of how `GradeReportStep` builds the zip:

- **Base names only.** `vectors/prng_py.csv` is listed as `prng_py.csv`, because
  the zip is flat and the autograder checks `submission_dir / name`. A config
  entry containing a directory can never match, and `build_lab_autograder`
  rejects one.
- **Do not list `submitted_results.json`.** `autograde.py` checks for it
  separately, after this list.

Keep this in step with the step's `bundle`. Nothing enforces that coupling: add
a file to `bundle` and forget the config and students see "Missing required
submission files" for something they did submit.

### 2. Build the zip

```bash
cd labs/prng
build_lab_autograder
```

```
template: C:\Users\sdran\Documents\repos\hwdesign\gradescope
created:  C:\Users\sdran\Documents\repos\hwdesign-soln\labs\prng\autograder.zip
a submission must contain 6 file(s): prng_model.py, prng_eval.py, prng_next.sv,
tb_prng.sv, prng_py.csv, prng_hist.png
```

This is a `hwdesign` console script, so it needs the **hwdesign venv**, not the
one you use for the grader portal. It writes `autograder_build/` — the shared
`gradescope/` template plus your config — and zips it:

```
autograder.zip
    autograde.py            the shared template, identical for every lab
    autograder_config.xml   yours
    requirements.txt
    run_autograder
    setup.sh
```

Both `autograder_build/` and `autograder.zip` are gitignored build output. The
config is source and belongs in the repository.

| Option | Meaning |
|---|---|
| `--config PATH` | A differently-named config (default: `autograder_config.xml` in this directory) |
| `--shared DIR` | The `gradescope/` template directory. Found by searching upward from the installed package by default |

### 3. Create the Gradescope assignment

- **Assignments → Create Assignment → Programming Assignment**
- **Autograder Points**: the sum of every graded step's `points` — 30 for prng
  (10 + 10 + 10). `python <lab>_build.py --grades` prints the total
- Uncheck **manual grading**
- **Configure autograder → zip file upload**, choose `autograder.zip`, **Update
  Autograder**, and wait for the build
- Under **Review Grades**, **Publish Grades** once, so students see their score
  on submission

### 4. Test it

Build the lab yourself and upload the submission it produces:

```bash
cd labs/prng
python prng_build.py
# → submission/submission.zip
```

Then **Configure Autograder → Test autograder** and upload that zip. Gradescope
should display the same total and the same per-stage breakdown the build printed,
because the autograder does nothing but read the file. If it shows something
else — most often 0 — the required-files list and the bundle have drifted apart.

---

## The limits of this model

**Scores are computed on the student's machine.** `autograde.py` copies
`submitted_results.json` verbatim; it never re-runs anything. The required-files
list is the only check, and there is no signature. A student who edits that JSON
gets whatever they typed.

This is a deliberate trade — running Vivado inside a Gradescope container is not
practical — but it means the lab autograder is a *completeness* check and a
convenience, not an integrity check. It is not comparable to the
[unit autograder](https://sdrangan.github.io/llmgrader/docs/admin/gradescope/),
which signs its submissions. Treat lab scores as self-reported and spot-check
the bundled source, which is why `bundle` ships the student's actual files and
their histogram alongside the numbers.

**Nothing validates the config against the DAG.** The two lists are coupled by
convention. Deriving `required_files` from the step's `bundle` would close this;
it has not been done yet.
